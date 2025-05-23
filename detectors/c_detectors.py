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
from os import environ
from traceback import format_exc
from logging import getLogger
from time import time
from setproctitle import setproctitle
from streams.redis import my_redis as streams_redis
#from psutil import virtual_memory

from tools.c_spawn import viewable

class c_detector(viewable):
  def __init__(self, dbline, ev_detectorq, logger, ):
    from tools.c_tools import c_buffer
    self.type = 'D'
    self.dbline = dbline
    self.id = dbline.id
    if self.dbline.cam_virtual_fps:
      self.dataqueue = c_buffer()
    else:  
      self.dataqueue = c_buffer(
        block_put = False, 
        #debug = 'Det' + str(self.id), 
      )
    self.ev_detectorq = ev_detectorq
    self.scaledown = self.get_scale_down()
    super().__init__(logger, )
  
  async def run_here(self): #Run on the original (=Main-) Process 
    await super().run_here()
   
  async def async_runner(self):
    import django
    django.setup()
    from tools.l_break import a_break_type, BR_MEDIUM
    from tools.c_logger import alog_ini
    from tools.c_tools import rect_atob, rect_btoa, merge_rects
    self.merge_rects = merge_rects
    self.rect_atob = rect_atob
    self.rect_btoa = rect_btoa
    try:
      self.logname = 'detector #'+str(self.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Detector #' + str(self.id))
      await super().async_runner() 
      self.firstdetect = True
      self.ts_background = time()
      self.finished = True
      self.cam_xres = self.dbline.cam_xres
      self.cam_yres = self.dbline.cam_yres
      self.run_lock = False
      self.adapt_fact = 1.5
      environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
      if self.dbline.det_gpu_nr_cv == -1:
        environ["CUDA_VISIBLE_DEVICES"] = ''
      else:  
        environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.det_gpu_nr_cv)
      self.logger.info('**** Detector #' + str(self.id)+' running GPU #' 
        + str(self.dbline.det_gpu_nr_cv))
      self.do_run = True
      self.warning_done = False
      #print('Launch: detector')
      while self.do_run:
        frameline = await self.run_one(await self.dataqueue.get())
        if frameline:
          if self.dbline.det_view and streams_redis.view_from_dev('D', self.id):
            await self.viewer.inqueue.put(frameline)
      self.dataqueue.stop()
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())
    
  async def process_received(self, received):  
    result = True
    if (received[0] == 'set_fpslimit'):
      self.dbline.det_fpslimit = received[1]
      if received[1] == 0:
        self.sl.period = 0.0
      else:
        self.sl.period = 1.0 / received[1]
    elif (received[0] == 'set_mask'):
      mydrawpad = self.viewer.drawpad
      mydrawpad.ringlist = received[1]
      mydrawpad.make_screen()
      mydrawpad.mask_from_polygons()
    elif (received[0] == 'set_apply_mask'):
      self.dbline.det_apply_mask = received[1]
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
    elif (received[0] == 'reset'):
      while self.run_lock:
        await break_type(BR_MEDIUM)
      self.run_lock = True  
      await self.dbline.arefresh_from_db()
      self.scaledown = self.get_scale_down()
      self.firstdetect = True
      self.run_lock = False
    else:
      result = False  
    return(result)

  async def run_one(self, input):
    try:
      if input is None or input[2] == 0.0:
        return(None)
      frametime = input[2]
      if not (self.do_run and self.sl.greenlight(frametime)):
        return(None)
      if self.run_lock and not self.dbline.cam_virtual_fps: 
        return(None)
      self.run_lock = True
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
      erosion = self.dbline.det_erosion
      if (erosion > 0) :
        kernel = np.ones((erosion*2 + 1,erosion*2 + 1),np.uint8)
        buffer2 = cv.erode(buffer1,kernel,iterations =1)
      else:
        buffer2 = buffer1
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
                rectb = self.rect_atob(recta)
                rect_list.append(rectb)
                recta = self.rect_btoa(rectb)
      if rect_list:          
        rect_list = self.merge_rects(rect_list)
        with self.ev_detectorq.multi_put_lock:
          for rect in rect_list[:self.dbline.det_max_rect]:
            recta = self.rect_btoa(rect)
            cv.rectangle(buffer1, recta, (200), self.linewidth)
            if ((recta[2]<=objectmaxsize) and (recta[3]<=objectmaxsize)):
              if not streams_redis.check_if_counts_zero('E', self.id):
                if self.scaledown > 1:
                  rect = [item * self.scaledown for item in rect]
                aoi = np.copy(frameall[rect[2]:rect[3], rect[0]:rect[1]])
                await self.ev_detectorq.put((
                  3, aoi, frametime, rect, cv.imencode('.bmp', aoi)[1].tobytes(),
                ))  
            else:
              self.background = np.float32(frame)
          if not streams_redis.check_if_counts_zero('E', self.id):
            await self.ev_detectorq.put('stop') 
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
        await self.dbline.asave(update_fields = ['det_fpsactual', ])
        streams_redis.fps_to_dev(self.type, self.id, fps)
      self.run_lock = False
      return([3, buffer1, frametime])
    except:
      self.logger.error(format_exc())
      
  def get_scale_down(self): 
    result = self.dbline.det_scaledown
    if not result:
      if (self.dbline.cam_xres >= 2560) or (self.dbline.cam_yres >= 2560):
        result = 4
      elif (self.dbline.cam_xres >= 1280) or (self.dbline.cam_yres >= 1280):
        result = 2
      else:
        result = 1
    self.xres = self.dbline.cam_xres // result
    self.yres = self.dbline.cam_yres // result
    if result >= 4:
      self.linewidth = 3
    elif result >= 2:
      self.linewidth = 4
    else:
      self.linewidth = 5 
    return(result)      
      
  def reset(self):  
    self.inqueue.put(('reset', ))

  def stop(self):
    self.dataqueue.stop()
    super().stop()

