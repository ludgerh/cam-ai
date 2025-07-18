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

import numpy as np
import cv2 as cv
import asyncio
import aiofiles
import aiofiles.os
from datetime import datetime
from random import randint
from os import path, makedirs
from time import time
from collections import OrderedDict
from threading import Lock as t_lock
from django.conf import settings
from django.utils import timezone
from channels.db import database_sync_to_async
from tools.l_tools import ts2filename, uniquename_async, np_mov_avg, djconf
from tools.l_crypt import l_crypt
from tools.l_smtp import l_smtp, l_msg
from tools.c_tools import do_reduction, aget_smtp_conf
from tools.tokens import maketoken_async
from schools.c_schools import get_taglist
from streams.models import stream as db_stream
from .models import event, event_frame

import os

async def resolve_rules(conditions, predictions):
  if predictions is None:
    return(False)
  if len(conditions) > 0:
    cond_str = '' 
    for item in conditions:
      if cond_str:
        if item['and_or'] == 1:
          cond_str += ' and '
        else:
          cond_str += ' or '
      if item['bracket'] > 0:
        cond_str += '(' * item['bracket']


      if item['c_type'] == 1:
        item_result = True
      elif item['c_type'] == 2:
        count = 0
        item_result = False
        for prediction in predictions:
          if prediction >= item['y']:
            count += 1
            if count >= item['x']:
              item_result = True
              break
      elif item['c_type'] == 3:
        count = 0
        item_result = False
        for prediction in predictions:
          if prediction < item['y']:
            count += 1
            if count >= item['x']:
              item_result = True
              break
      elif item['c_type'] == 4:
        item_result = (predictions[item['x']] >= item['y'])
      elif item['c_type'] == 5:
        item_result = (predictions[item['x']] < item['y'])
      elif item['c_type'] == 6:
        myprediction = predictions[item['x']]
        count = 0
        item_result = True
        for prediction in predictions:
          if prediction > myprediction:
            count += 1
            if count >= item['y']:
              item_result = False
              break
      cond_str += str(item_result)


      if item['bracket'] < 0: 
        cond_str += ')' * (-1 * item['bracket'])
    return(eval(cond_str))
  else:
    return(False)

class c_event(list):
  crypt = None

  def __init__(self, tf_worker, tf_w_index, frame, margin, eventer_dbl, school_nr, 
      idx, logger):
    self.event_lock = t_lock()
    with self.event_lock:
      super().__init__()
      self.id = idx
      self.tf_worker = tf_worker
      self.eventer_id = eventer_dbl.id
      self.eventer_name = eventer_dbl.name
      self.tf_w_index = tf_w_index
      self.xmax = eventer_dbl.cam_xres - 1
      self.ymax = eventer_dbl.cam_yres - 1
      self.margin = margin
      self.isrecording = False
      self.goes_to_school = False
      self.to_email = ''
      self.ts = None
      self.savename = ''
      self.schoolnr = eventer_dbl.eve_school.id
      self.dbline = event()
      self.dbline.camera = eventer_dbl
      self.dbline.start=timezone.make_aware(datetime.fromtimestamp(time()))
      self.start = frame[2]
      self.end = frame[2]
      self.append(max(0, frame[3][0] - margin))
      self.append(min(self.xmax, frame[3][1] + margin))
      self.append(max(0, frame[3][2] - margin))
      self.append(min(self.ymax, frame[3][3] + margin))
      self.append([frame[5]]) #Predictions
      self.logger = logger
      self.frames = OrderedDict([(0, frame)])
      self.last_frame_index = 1
      self.shrink_factor = eventer_dbl.eve_shrink_factor
      self.focus_max = np.max(frame[5][1:])
      self.focus_time = frame[2]
      self.check_out_ts = None
      self.dirs_checked = False
  
  @classmethod  
  async def create(cls, tf_worker, tf_w_index, frame, margin, eventer_dbl, school_nr, 
      idx, logger):
    instance = cls(tf_worker, tf_w_index, frame, margin, eventer_dbl, school_nr, 
      idx, logger)
    instance.stream_creator = await database_sync_to_async(lambda: instance.dbline.camera.creator)()
    if c_event.crypt is None:
      if instance.dbline.camera.encrypted:
        if instance.dbline.camera.crypt_key:
          c_event.crypt = l_crypt(key=instance.dbline.camera.crypt_key)
        else:
          c_event.crypt = l_crypt()
          instance.dbline.camera.crypt_key = c_event.crypt.key
          await instance.dbline.camera.asave(update_fields=['crypt_key'])
    await instance.a_init()   
    return instance 
    
  async def a_init(self): 
    if not self.dirs_checked:
      self.dirs_checked = True
      self.datapath = await djconf.agetconfig('datapath', 'data/')
      self.schoolpath = await djconf.agetconfig('schoolframespath', self.datapath + 'schoolframes/')
      self.clienturl = settings.CLIENT_URL
      for i in range(100):
        pathadd = str(self.dbline.camera.id) + '/' + str(i)
        await aiofiles.os.makedirs(self.schoolpath + pathadd, exist_ok=True)
      self.number_of_frames = await djconf.agetconfigint('frames_event', 32) 
    self.tag_list = await database_sync_to_async(get_taglist)(self.schoolnr)

  def add_frame(self, frame):
    with self.event_lock:
      s_factor = self.shrink_factor
      if (frame[3][0] - self.margin) <= self[0]:
        self[0] = max(0, frame[3][0] - self.margin)
      else:
        self[0] = round(((frame[3][0] - self.margin) * s_factor + self[0]) 
          / (s_factor+1.0))
      if (frame[3][1] + self.margin) >= self[1]:
        self[1] = min(self.xmax, frame[3][1] + self.margin)
      else:
        self[1] = round(((frame[3][1] + self.margin) * s_factor + self[1]) 
          / (s_factor+1.0))
      if (frame[3][2] - self.margin) <= self[2]:
        self[2] = max(0, frame[3][2] - self.margin)
      else:
        self[2] = round(((frame[3][2] - self.margin) * s_factor + self[2]) 
          / (s_factor+1.0))
      if (frame[3][3] + self.margin) >= self[3]:
        self[3] = min(self.ymax, frame[3][3] + self.margin)
      else:
        self[3] = round(((frame[3][3] + self.margin) * s_factor + self[3]) 
          / (s_factor+1.0))
      self.end = frame[2]
      self[4].append(frame[5]) 
      self.frames[self.last_frame_index] = frame
      self.last_frame_index += 1
      if (new_max := np.max(frame[5][1:])) > self.focus_max:
        self.focus_max = new_max
        self.focus_time = frame[2]

  def merge_frames(self, the_other_one):
    self.frames = {**self.frames, **the_other_one.frames}
    self.frames = OrderedDict(sorted(self.frames.items(), key=lambda x: x[1][2]))
    if the_other_one.focus_max > self.focus_max:
      self.focus_max = the_other_one.focus_max
      self.focus_time = the_other_one.focus_time

  async def pred_read(self, radius=3, max=None, ave=None, last=None):
    result2 = np.zeros((len(self.tag_list)), np.float32)
    if self[4]:
      result1 = np.vstack(self[4])
      if radius > 0:
        result1 = np_mov_avg(result1, radius)
      if max is not None:
        result2 += np.max(result1, axis=0) * max
      if ave is not None:
        result2 += np.average(result1, axis=0) * ave
      if last is not None:
        result2 += result1[-1] * last
      return(np.clip(result2, 0.0, 1.0))
    else:
      return(result2)

  async def p_string(self):
    predictions = await self.pred_read(max=1.0)
    predline = '['
    for i in range(len(self.tag_list)):
      if (predictions[i] >= 0.5):
        if (predline != '['):
          predline += ', '
        predline += str(self.tag_list[i].name)[:3]
    return(predline+']')

  async def frames_filter(self, outlength, cond_dict):  
    sortindex = [x for x in self.frames if (
      await resolve_rules(cond_dict[2],  self.frames[x][5])
        or await resolve_rules(cond_dict[3], self.frames[x][5])
        or await resolve_rules(cond_dict[4],  self.frames[x][5])
    )] 
    if len(sortindex) > outlength:
      sortindex.sort(key=lambda x: np.max(self.frames[x][5][1:]), reverse=True) #prediction
      sortindex = sortindex[:outlength]
      sortindex.sort(key=lambda x: self.frames[x][2]) #timestamp
    self.frames = OrderedDict([(x, self.frames[x]) for x in sortindex])
    
  async def process_frame(self, frame):
    pathadd = str(self.dbline.camera.id) + '/' + str(randint(0,99))
    filename = await uniquename_async(
      self.schoolpath, 
      pathadd + '/' + ts2filename(frame[2], noblank=True), 
      'bmp', 
    )
    bmp_data =  frame[4]
    if c_event.crypt is not None:
      bmp_data = c_event.crypt.encrypt(bmp_data)
    async with aiofiles.open(self.schoolpath+filename, "wb") as f:
      await f.write(bmp_data)
    frameline = event_frame(
      time = timezone.make_aware(datetime.fromtimestamp(frame[2])),
      name = filename,
      encrypted = c_event.crypt is not None,
      x1 = frame[3][0],
      x2 = frame[3][1],
      y1 = frame[3][2],
      y2 = frame[3][3],
      event = self.dbline,
    )
    await frameline.asave()
    if self.to_email:
      frame.append(frameline.id)

  async def save(self, cond_dict):
    #print('*** Saving Event:', self.id)
    await self.frames_filter(self.number_of_frames, cond_dict)
    frames_to_save = self.frames.values()
    self.dbline.p_string = (self.eventer_name+'('+str(self.eventer_id)+'): '
      + await self.p_string())
    self.dbline.start=timezone.make_aware(datetime.fromtimestamp(self.start))
    self.dbline.end=timezone.make_aware(datetime.fromtimestamp(self.end))
    self.dbline.xmin=self[0]
    self.dbline.xmax=self[1]
    self.dbline.ymin=self[2]
    self.dbline.ymax=self[3]
    self.dbline.numframes=len(frames_to_save)
    self.dbline.done = not self.goes_to_school
    await self.dbline.asave()
    await asyncio.gather(*(self.process_frame(frame) for frame in frames_to_save))
    if self.to_email:
      self.mailimages = []
      for frame in frames_to_save:
        imagedata = cv.imdecode(
          np.frombuffer(frame[4], dtype=np.uint8), cv.IMREAD_UNCHANGED
        )
        imagedata = do_reduction(imagedata, 200, 200)
        imagedata = cv.imencode('.jpg', imagedata)[1].tobytes()
        self.mailimages.append([frame[6], frame[2], imagedata, 'jpg', 'image'])
      await self.send_emails()

  async def send_emails(self):
    print('Sending Email:', self.to_email)
    self.to_email = self.to_email.split()
    for receiver in self.to_email:
      mytoken = await maketoken_async('EVR', self.dbline.id, receiver)
      subject = ('#'+str(self.eventer_id) + '(' + self.eventer_name + '): '
        + await self.p_string())
      to_email = receiver
      plain_text = 'Hello CAM-AI user,\n' 
      plain_text += 'We had some movement.\n'  
      if self.savename:
        plain_text += 'Here is the movie: \n' 
        plain_text += self.clienturl + 'schools/getbigmp4/' + str(self.dbline.id) + '/'
        plain_text += str(mytoken[0]) + '/' + mytoken[1] + '/video.html \n' 
      plain_text += 'Here are the images: \n'  
      for item in self.mailimages:
        plain_text += self.clienturl + 'schools/getbmp/0/' + str(item[0]) + '/3/1/200/200/'
        plain_text += str(mytoken[0]) + '/' + mytoken[1] + '/ \n' 
      html_text = '<html><body><p>Hello CAM-AI user, <br>\n' 
      html_text += 'We had some movement. <br> \n' 
      if self.savename:
        filepath = (djconf.getconfig('recordingspath', self.datapath + 'recordings/')
          + self.dbline.videoclip + '.jpg')
        if path.exists(filepath):
          with open(filepath, "rb") as f:
            jpegdata = f.read()
          jpegdata = cv.imdecode(
            np.frombuffer(jpegdata, dtype=np.uint8), cv.IMREAD_UNCHANGED
          )
          jpegdata = do_reduction(jpegdata, 400, 400)
          jpegdata = cv.imencode('.jpg', jpegdata)[1].tobytes()
          self.mailimages.append([0, None, jpegdata, 'jpeg', 'video'])
          html_text += '<br>Here is the movie (click on the image to see): <br> \n' 
          html_text += ('<a href="' + self.clienturl + 'schools/getbigmp4/' 
            + str(self.dbline.id) + '/')
          html_text += str(mytoken[0]) + '/' + mytoken[1] + '/video.html' 
          html_text += '" target="_blank">'
          html_text += '<img src="cid:image0" style="width: 400px; height: auto"></a> <br>\n'
        else:
          self.logger.error('JPG-File not found: ' + filepath)
      html_text += 'Here are the images: <br> \n'
      for item in self.mailimages:
        if item[4] == 'image':
          html_text += '<a href="' + self.clienturl + 'schools/getbigbmp/0/' + str(item[0]) + '/'
          html_text += str(mytoken[0]) + '/' + mytoken[1] + '/' 
          html_text += '" target="_blank">'
          html_text += ('<img src="cid:image' + str(item[0]) 
            + '" style="width: 200px; height: 200px; object-fit: contain"</a> \n')
      html_text += '<br> \n'
      smtp_conf = await aget_smtp_conf()
      my_smtp = l_smtp(**smtp_conf)
      await my_smtp.async_init()
      my_msg = l_msg(
        smtp_conf['sender_email'],
        receiver,
        subject,
        plain_text,
        html = html_text,
      )
      for item in self.mailimages:
        my_msg.attach_jpeg(item[2], 'image' + str(item[0]))  
      await my_smtp.sendmail(
        smtp_conf['sender_email'],
        receiver,
        my_msg,
      )
      if my_smtp.result_code:
        self.logger.error('SMTP: ' + my_smtp.answer)
        self.logger.error(str(my_smtp.last_error))
      await my_smtp.quit()

