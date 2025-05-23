"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""

import cv2 as cv
import numpy as np
import aiofiles
from time import time, sleep
from random import randint
from collections import deque
from django.db import connection
from django.db.utils import OperationalError
from l_buffer.l_buffer import l_buffer
from tools.models import setting as dbsetting
from tools.l_tools import djconf
from streams.redis import my_redis as streams_redis

def c_convert(frame, typein, typeout=0, xycontained=0, xout=0, yout=0, incrypt=None, 
  outcrypt=None):
# Frame Types:
# 1 : opencv Data
# 2 : BMP Data
# 3 : Jpeg Data
  if not typeout:
    typeout = typein
  if typein != 1:
    if incrypt:
      frame = incrypt.decrypt(frame)
    frame = cv.imdecode(np.frombuffer(frame, dtype=np.uint8), cv.IMREAD_UNCHANGED) #convert to opencv
  xin = frame.shape[1]
  yin = frame.shape[0]
  forcescale = False
  if xycontained:
    xscaling = xout / xin
    yscaling = yout / yin
    if xscaling < yscaling:
      xout = round(xin * xscaling)
      yout = round(yin * xscaling)
    else:
      xout = round(xin * yscaling)
      yout = round(yin * yscaling)
  else:
    if not xout:
      xout = xin
    if yout:
      forcescale = True
    else:
      yout = round(yin / xin * xout)
  if (xout < xin) or (yout < yin) or forcescale:
    frame = cv.resize(frame, (xout, yout)) #resize
  if typeout == 2:
    frame = cv.imencode('.bmp', frame)[1].tostring()
  elif typeout == 3:
    #encode_param = [int(cv.IMWRITE_JPEG_QUALITY), 100]
    #frame = cv.imencode('.jpg', frame, encode_param)[1].tostring()
    frame = cv.imencode('.jpg', frame)[1].tostring()
  #print('*****', len(frame))  
  return(frame)


class speedlimit:
  def __init__(self, period = 1.0):
    self.ts = 0.0
    self.rest = 0.0
    self.period = period

  def greenlight(self, frame_time):
    if not self.period:
      return(True)
    difference = self.rest + frame_time - self.ts
    if difference >= self.period:
      self.ts = frame_time
      self.rest = difference % self.period
      return(True)
    else:
      return(False)  

class speedometer:
  def __init__(self, count = 10):
    self.count = count
    self.times_deque = deque()
    self.ts2 = time()

  def gettime(self):
    self.ts1 = self.ts2
    self.ts2 = time()
    if len(self.times_deque) >= self.count:
      self.times_deque.popleft()
    self.times_deque.append(self.ts2 - self.ts1)
    return(len(self.times_deque) / sum(self.times_deque))

def rect_atob(rect):
	# Rectangle notation B: (x1, x2, y1, y2)
	return([rect[0], rect[0]+rect[2]-1, rect[1], rect[1]+rect[3]-1])

def rect_btoa(rect):
	# Rectangle notation A: (x1, y1, w, h)
	return([rect[0], rect[2], rect[1]-rect[0]+1, rect[3]-rect[2]+1])

def hasoverlap(rect1, rect2) : # Rectangles in notation B
	if ((rect1[1] >= rect2[0]) and (rect2[1] >= rect1[0]) 
    and (rect1[3] >= rect2[2]) and (rect2[3] >= rect1[2])):
		return(True)
	else :
		return(False)

def merge_rects(rect_list): # Rectangles in notation B
  while True:
    changed = False
    for i in range(len(rect_list)):
      if rect_list[i][0] > -1:
        for j in range(i+1, len(rect_list)):
          if ((rect_list[j][0] > -1) 
              and hasoverlap(rect_list[i], rect_list[j])):
            rect_list[i][0] = min(rect_list[i][0], rect_list[j][0])
            rect_list[i][1] = max(rect_list[i][1], rect_list[j][1])
            rect_list[i][2] = min(rect_list[i][2], rect_list[j][2])
            rect_list[i][3] = max(rect_list[i][3], rect_list[j][3])
            rect_list[j][0] = -1
            changed = True
    if not changed:
      break
  rect_list = [item for item in rect_list if item[0] > -1]
  return(rect_list)

def hasoverlap(rect1, rect2) : # Rectangles in notation B
	if ((rect1[1] >= rect2[0]) and (rect2[1] >= rect1[0]) 
    and (rect1[3] >= rect2[2]) and (rect2[3] >= rect1[2])):
		return(True)
	else :
		return(False)
  
def image_size(infile):
  myimage = cv.imread(infile)
  xin = myimage.shape[1]
  yin = myimage.shape[0]
  return(xin, yin)
  
def do_reduction(image, x, y):
  xin = image.shape[1]
  yin = image.shape[0]
  #print('In:', image.shape, x, y, xin, yin) 
  if (xin > x or yin > y) and (x > 0 and y > 0):
    if (x / xin) > (y / yin):
      scale = x / xin
    else:
      scale = y / yin
    return(cv.resize(image, (round(xin * scale), round(yin * scale)))) 
  else:  
    return(image) 
  
def reduce_image(infile, outfile, x=0, y=0, crypt=None):
  if outfile is None:
    outfile = infile
  if crypt:
    with open(infile, "rb") as f:
      myimage = f.read()
    myimage = crypt.decrypt(myimage)
    myimage = cv.imdecode(np.frombuffer(myimage, dtype=np.uint8), cv.IMREAD_UNCHANGED)
  else:    
    myimage = cv.imread(infile)
  myimage = do_reduction(myimage, x, y) 
  cv.imwrite(outfile, myimage)
  
async def reduce_image_async(infile, outfile, x=0, y=0, crypt=None):
  if outfile is None:
    outfile = infile
  async with aiofiles.open(infile, mode="rb") as f:
    myimage = await f.read()
  if crypt:
    myimage = crypt.decrypt(myimage)
  myimage = cv.imdecode(np.frombuffer(myimage, dtype=np.uint8), cv.IMREAD_UNCHANGED)
  myimage = do_reduction(myimage, x, y) 
  myimage = cv.imencode('.bmp', myimage)[1].tobytes()
  async with aiofiles.open(outfile, mode="wb") as f:
    await f.write(myimage)
  
def list_from_queryset(qs, logger = None):
  result = [] 
  for item in qs:
    result.append(item)
  return(result) 
  
def get_smtp_conf(extended_from = True):  
  sender_email = djconf.getconfig('smtp_email', forcedb=True)
  if extended_from:
    sender_email = 'CAM-AI Emailer<' + sender_email + '>'
  return({
  'host' : djconf.getconfig('smtp_server', forcedb=True), 
  'port' : djconf.getconfigint('smtp_port', forcedb=True),
  'user' : djconf.getconfig('smtp_account', forcedb=True),
  'password' : djconf.getconfig('smtp_password', forcedb=True),
  'sender_email' : sender_email,
  })
  
async def aget_smtp_conf(extended_from = True):  
  sender_email = await djconf.agetconfig('smtp_email', forcedb=True)
  if extended_from:
    sender_email = 'CAM-AI Emailer<' + sender_email + '>'
  return({
  'host' : await djconf.agetconfig('smtp_server', forcedb=True), 
  'port' : await djconf.agetconfigint('smtp_port', forcedb=True),
  'user' : await djconf.agetconfig('smtp_account', forcedb=True),
  'password' : await djconf.agetconfig('smtp_password', forcedb=True),
  'sender_email' : sender_email,
  })

"""
struct = coded list of transferred data blocks:
  O --> Python object
  L --> Large Python Object, going through shared memory
  B --> Bytes, variable length
  N --> Numpy array
  
m_proc: Use multiprocessing queues (default = True)
q_len: Length of data queue (default = 1), None: no queue (only if not m_proc)
block_put: Block put() until the previous data was read (default = True)
block_get: Block get() until new data (default = True)
put_timeout: Return after x seconds if blocked (default = None)
get_timeout: Return after x seconds if blocked (default = None)
call: Callback on the get side (default = None)
debug: Debug level (default = 0 (no debug output))
"""
     
class c_buffer(l_buffer):
  def __init__(self, **kwargs):
    return super().__init__(('NO'), **kwargs)
  
  async def put(self, frame):
    objects = [frame[0]] + frame[2:]
    await super().put((frame[1], objects, ))
    
  async def get(self, **kwargs):
    if (result := await super().get(**kwargs)):
      frame = [result[1][0], result[0]] + result[1][1:]
    else:
      frame = None  
    return(frame)
    
debug = False    

def add_view_count(type, idx):
  streams_redis.inc_view_dev(type, idx)
  if debug:
    print('Vie+', type, idx, streams_redis.view_from_dev(type, idx))
  if type == 'D':
    add_data_count('C', idx)
  if type == 'E':
    add_data_count('D', idx)

def take_view_count(type, idx):
  streams_redis.dec_view_dev(type, idx)
  if debug:
    print('Vie-', type, idx, streams_redis.view_from_dev(type, idx))
  if type == 'D':
    take_data_count('C', idx)
  if type == 'E':
    take_data_count('D', idx)

def add_record_count(type, idx):
  if type == 'E':
    change = (streams_redis.record_from_dev('E', idx) == 0)
    streams_redis.set_record_dev('E', idx, 1)
  else:
    change = True
    streams_redis.inc_record_dev(type, idx)
  if debug:
    print('Rec+', type, idx, streams_redis.record_from_dev(type, idx))
  if change:  
    if type == 'D':
      add_record_count('C', idx)
    if type == 'E':
      add_record_count('D', idx)

def take_record_count(type, idx):
  if type == 'E':
    change = (streams_redis.record_from_dev('E', idx) == 1)
    streams_redis.set_record_dev('E', idx, 0)
  else:
    change = True
    streams_redis.dec_record_dev(type, idx)
  if debug:
    print('Rec-', type, idx, streams_redis.record_from_dev(type, idx))
  if change:  
    if type == 'D':
      take_record_count('C', idx)
    if type == 'E':
      take_record_count('D', idx)

def add_data_count(type, idx):
  if type == 'E':
    change = (streams_redis.data_from_dev('E', idx) == 0)
    streams_redis.set_data_dev('E', idx, 1)
  else:
    change = True
    streams_redis.inc_data_dev(type, idx)
  if debug:
    print('Dat+', type, idx, streams_redis.data_from_dev(type, idx))
  if change:  
    if type == 'D':
      add_data_count('C', idx)
    if type == 'E':
      add_data_count('D', idx)

def take_data_count(type, idx):
  if type == 'E':
    change = (streams_redis.data_from_dev('E', idx) == 1)
    streams_redis.set_data_dev('E', idx, 0)
  else:
    change = True
    streams_redis.dec_data_dev(type, idx)
  if debug:
    print('Dat-', type, idx, streams_redis.data_from_dev(type, idx))
  if change:  
    if type == 'D':
      take_data_count('C', idx)
    if type == 'E':
      take_data_count('D', idx)
        

        
