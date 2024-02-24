"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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
from time import time, sleep
from shutil import copy
from tools.l_tools import djconf

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
    frame = cv.imdecode(np.frombuffer(frame, dtype=np.uint8), cv.IMREAD_UNCHANGED)
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
    frame = cv.resize(frame, (xout, yout))
  if typeout == 2:
    frame = cv.imencode('.bmp', frame)[1].tostring()
  elif typeout == 3:
    frame = cv.imencode('.jpg', frame)[1].tostring()
  return(frame)


class speedlimit:
  def __init__(self):
    self.ts2 = 0.0
    self.rest = 0.0

  def greenlight(self, time_span, frame_time):
    if time_span == 0.0:
      return(True)
    else:
      self.ts1 = self.ts2
      self.ts2 = frame_time
      self.rest = self.rest + time_span + self.ts1 - self.ts2
      if self.rest < 0.0:
        self.rest = 0.0
      if self.rest >= time_span:
        self.rest -= time_span
        return(False)
      else:
        return(True)

class speedometer:
  def __init__(self):
    self.ts1 = 0
    self.ts2 = time()
    self.counter = 0
    self.timeadd = 0.0

  def gettime(self):
    if self.ts1 == 0:
      result = 0.0
    else:
      self.counter += 1
      self.timeadd += (self.ts2 - self.ts1)
      if self.timeadd >= 10:
        result = (self.counter / self.timeadd)
        self.counter = 0
        self.timeadd = 0.0
      else:
        result = None
    self.ts1 = self.ts2
    self.ts2 = time()
    return(result)

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
  
def reduce_image(infile, outfile, x, y, crypt=None):
  if outfile is None:
    outfile = infile
  if crypt:
    with open(infile, "rb") as f:
      myimage = f.read()
    myimage = crypt.decrypt(myimage)
    myimage = cv.imdecode(np.frombuffer(myimage, dtype=np.uint8), cv.IMREAD_UNCHANGED)
  else:    
    myimage = cv.imread(infile)
  xin = myimage.shape[1]
  yin = myimage.shape[0]
  #print('In:', myimage.shape, x, y, xin, yin) 
  if (xin > x) or (yin > y):
    if (x / xin) > (y / yin):
      scale = x / xin
    else:
      scale = y / yin
    myimage = cv.resize(myimage, (round(xin * scale), round(yin * scale)))  
  cv.imwrite(outfile, myimage)
  #print('Out:', myimage.shape) 
  
