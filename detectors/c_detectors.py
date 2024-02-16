# Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import numpy as np
import cv2 as cv
from os import environ
from traceback import format_exc
from logging import getLogger
from time import time, sleep
from setproctitle import setproctitle
from django.db import connection
from django.db.utils import OperationalError
from tools.l_tools import djconf
from tools.c_tools import rect_atob, rect_btoa, hasoverlap, merge_rects
from tools.c_logger import log_ini
from l_buffer.l_buffer import l_buffer
from viewers.c_viewers import c_viewer
from streams.c_devices import c_device
from streams.models import stream


class c_detector(c_device):
  def __init__(self, *args, **kwargs):
    try:
      self.type = 'D'
      super().__init__(*args, **kwargs)
      self.mode_flag = self.dbline.det_mode_flag
      self.dataqueue = l_buffer(1, block=True)
      self.firstdetect = True
      self.ts_background = time()
      self.finished = True
      self.cam_xres = self.dbline.cam_xres
      self.cam_yres = self.dbline.cam_yres
      myscaledown = self.dbline.det_scaledown
      if not myscaledown:
        if (self.cam_xres >= 2560) or (self.cam_yres >= 2560):
          myscaledown = 4
        elif (self.cam_xres >= 1280) or (self.cam_yres >= 1280):
          myscaledown = 2
        else:
          myscaledown = 1
      self.scaledown = myscaledown   
      if self.dbline.det_view:
        self.viewer = c_viewer(self, self.logger)
      else:
        self.viewer = None
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def in_queue_handler(self, received):
    if super().in_queue_handler(received):
      return(True)
    else:
      if (received[0] == 'set_fpslimit'):
        self.dbline.det_fpslimit = received[1]
        if received[1] == 0:
          self.period = 0.0
        else:
          self.period = 1.0 / received[1]
      elif (received[0] == 'set_threshold'):
        self.dbline.det_threshold = received[1]
      elif (received[0] == 'set_backgr_delay'):
        self.dbline.det_backgr_delay = received[1]
      elif (received[0] == 'set_dilation'):
        self.dbline.det_dilation = received[1]
      elif (received[0] == 'set_erosion'):
        self.dbline.det_erosion = received[1]
      elif (received[0] == 'set_max_size'):
        self.dbline.det_fmax_size = received[1]
      elif (received[0] == 'set_max_rect'):
        self.dbline.det_max_rect = received[1]
      else:
        return(False)
      return(True)

  def run(self):
    self.xres = self.cam_xres // self.scaledown
    self.yres = self.cam_yres // self.scaledown
    if self.scaledown >= 4:
      self.linewidth = 3
    elif self.scaledown >= 2:
      self.linewidth = 4
    else:
      self.linewidth = 5
    super().run()

  def runner(self):
    try:
      super().runner()
      self.logname = 'detector #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      log_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Detector #'+str(self.dbline.id))
      if self.dbline.det_gpu_nr_cv:
        environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.det_gpu_nr_cv)
        self.logger.info('**** Detector running GPU #' + str(self.dbline.det_gpu_nr_cv))
      self.do_run = True
      self.warning_done = False
      while self.do_run:
        frameline = self.run_one(self.dataqueue.get())
        if frameline is None:
          sleep(djconf.getconfigfloat('short_brake', 0.1))
        else:
          if self.dbline.det_view and self.redis.view_from_dev('D', self.dbline.id):
            self.viewer.inqueue.put(data=frameline)
      self.dataqueue.stop()
      self.finished = True
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()
    self.logger.info('Finished Process '+self.logname+'...')
    self.logger.handlers.clear()

  def run_one(self, input):
    try:
      if input is None:
        return(None)
      print('Queuesize:', self.myeventer.detectorqueue.qsize())
      if self.myeventer.detectorqueue.qsize() > 5 * self.dbline.det_max_rect:
        if not self.warning_done:
          self.logger.warning('Detector #' + str(self.id)
            + ' skipped cycle, eventer queue > ' 
            + str(5 * self.dbline.det_max_rect))
          self.warning_done = True  
        return(None)  
      frametime = input[2]
      if not (self.do_run and self.sl.greenlight(self.period, frametime)):
        return(None)
      frame = input[1]
      frameall = frame
      if self.firstdetect:
        if self.scaledown > 1:
          self.buffer = cv.resize(
            frame, 
            (self.xres, self.yres), 
            interpolation=cv.INTER_NEAREST,
          )
        else:
          self.buffer = frame
        self.background = np.float32(self.buffer)
        self.firstdetect = False
      if self.scaledown > 1:
        frame = cv.resize(frame, (self.xres, self.yres), interpolation=cv.INTER_NEAREST)
      if self.dbline.det_apply_mask and (self.viewer.drawpad.mask is not None):
        frame = cv.bitwise_and(frame, self.viewer.drawpad.mask)
      objectmaxsize = round(max(
        self.buffer.shape[0],
        self.buffer.shape[1],
      ) * self.dbline.det_max_size,)
      buffer1 = cv.absdiff(self.buffer, frame)
      buffer1 = cv.split(buffer1)
      buffer2 = cv.max(buffer1[0], buffer1[1])
      buffer1 = cv.max(buffer2, buffer1[2])
      ret, buffer1 = cv.threshold(buffer1,self.dbline.det_threshold,255,cv.THRESH_BINARY)
      if self.scaledown > 1:
      	erosion = round(self.dbline.det_erosion / self.scaledown)
      else:
      	erosion = self.dbline.det_erosion
      if (erosion > 0) :
        kernel = np.ones((erosion*2 + 1,erosion*2 + 1),np.uint8)
        buffer2 = cv.erode(buffer1,kernel,iterations =1)
      else:
        buffer2 = buffer1
      if self.scaledown > 1:
      	dilation = round(self.dbline.det_dilation / self.scaledown)
      else:
      	dilation = self.dbline.det_dilation
      if (dilation > 0) :
        kernel = np.ones((dilation*2 + 1,dilation*2 + 1),np.uint8)
        buffer3 = cv.dilate(buffer2,kernel,iterations =1)
      else:
        buffer3 = buffer2
      mask = 255 - buffer3
      buffer1 = cv.cvtColor(buffer1, cv.COLOR_GRAY2BGR)
      buffer2 = cv.cvtColor(buffer2, cv.COLOR_GRAY2BGR) 
      buffer4 = cv.cvtColor(buffer3, cv.COLOR_GRAY2BGR)
      buffer1 = list(cv.split(buffer1))
      buffer1[1] = buffer1[1] * 0
      buffer1 = cv.merge(buffer1)
      buffer1 = cv.addWeighted(buffer4, 0.2, buffer1, 1, 0)
      buffer1 = cv.addWeighted(buffer1, 1, buffer2, 1, 0)
      rect_list = []
      if dilation == 0:
        grid = 2
      else:
        grid = dilation*2
      xmax = buffer3.shape[1]-1
      for x in range(0,xmax+grid,grid):
        if x < xmax + grid:
          x = min(x, xmax)
          ymax = buffer3.shape[0]-1
          for y in range(0,ymax+grid,grid):
            if y < ymax + grid:
              y = min(y, ymax)
              if (buffer3[y,x] == 255) :
                retval, image, dummy, recta = cv.floodFill(buffer3, None,
                  (x, y), 100)
                rectb = rect_atob(recta)
                rectb.append(False)
                rect_list.append(rectb)
                recta = rect_btoa(rectb)
      rect_list = merge_rects(rect_list)
      sendtime = frametime
      for rect in rect_list[:self.dbline.det_max_rect]:
        recta = rect_btoa(rect)
        cv.rectangle(buffer1, recta, (200), self.linewidth)
        if ((recta[2]<=objectmaxsize) and (recta[3]<=objectmaxsize)):
          if not self.redis.check_if_counts_zero('E', self.dbline.id):
            if self.scaledown > 1:
              rect = [item * self.scaledown for item in rect]
            aoi = np.copy(frameall[rect[2]:rect[3], rect[0]:rect[1]])
            self.myeventer.detectorqueue.put(
              bytedata = aoi.tobytes(),
              objdata = (3, sendtime, rect[0], rect[1], rect[2], rect[3]),
            )  
          sendtime += 0.000001
        else:
          self.background = np.float32(frame)
      if self.dbline.det_backgr_delay == 0:
        self.buffer = frame
      else:
        if (time() >= (self.ts_background + self.dbline.det_backgr_delay)): 
          self.ts_background = time()
          cv.accumulateWeighted(frame, self.background, 0.1)
        else:
          cv.accumulateWeighted(frame, self.background, 0.5, mask)
        self.buffer = np.uint8(self.background)
      fps = self.som.gettime()
      if fps:
        self.dbline.det_fpsactual = fps
        mystreamline = stream.objects.filter(id = self.dbline.id)
        while True:
          try:
            mystreamline.update(det_fpsactual = fps)
            break
          except OperationalError:
            connection.close()
        self.redis.fps_to_dev(self.type, self.dbline.id, fps)
      return((3, buffer1, frametime))
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def getviewer(self):
    pass

  def stop(self):
    self.dataqueue.stop()
    super().stop()

