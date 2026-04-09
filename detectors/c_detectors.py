"""
Copyright (C) 2024-2026 by the CAM-AI team, info@cam-ai.de
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

import django
django.setup()
import asyncio
import numpy as np
import cv2 as cv
import json
import signal
from multiprocessing import Process as mp_process, SimpleQueue as s_queue
from os import environ
from logging import getLogger
from time import time
from setproctitle import setproctitle
from streams.redis import my_redis as streams_redis
from tf_workers.redis import my_redis as tf_workers_redis
from tools.c_logger import alog_ini
from globals.c_globals import add_viewer
from tools.c_spawn import viewable
from tools.c_tools import (
  rect_atob, 
  rect_btoa, 
  merge_rects, 
  c_buffer, 
  speedlimit, 
  speedometer, 
)
from tools.l_break import break_type, a_break_type, BR_SHORT, BR_MEDIUM, BR_LONG
from viewers.c_viewers import c_viewer
from drawpad.models import mask
from oneitem.shared_mem import shared_mem
from streams.models import stream

_SH_MEM_ITEMS = {
    'fps_limit' : 'd',
    'edit_active' : 'i',
    'threshold' : 'i',
    'backgr_delay' : 'i',
    'dilation' : 'i',
    'erosion' : 'i',
    'max_size' : 'i',
    'max_rect' : 'i',
    'apply_mask' : 'i',
    'aoi_xdim' : 'i',
    'aoi_ydim' : 'i',
    'scaledown' : 'i',
}

class c_detector():
  def __init__(self, dbline, myeventer, worker_id, logger, ):
    self.type = 'D'
    self.id = dbline.id
    add_viewer((my_viewer := c_viewer(self.type, self.id, logger,)))
    self.viewer = my_viewer
    self.viewer_queue = my_viewer.inqueue
    streams_redis.zero_to_dev(self.type, self.id)
    streams_redis.fps_to_dev(self.type, self.id, 0.0)
    self.shared_mem = shared_mem(
      source_dict = _SH_MEM_ITEMS, 
      shape = (dbline.cam_yres, dbline.cam_xres, 3), 
    )
    self.shared_mem.write_1_meta('fps_limit', dbline.det_fpslimit)
    self.shared_mem.write_1_meta('threshold', dbline.det_threshold)
    self.shared_mem.write_1_meta('backgr_delay', dbline.det_backgr_delay)
    self.shared_mem.write_1_meta('dilation', dbline.det_dilation)
    self.shared_mem.write_1_meta('erosion', dbline.det_erosion)
    self.shared_mem.write_1_meta('max_size', dbline.det_max_size)
    self.shared_mem.write_1_meta('max_rect', dbline.det_max_rect)
    self.shared_mem.write_1_meta('apply_mask', dbline.det_apply_mask)
    self.shared_mem.write_1_meta('scaledown', 0)
    self.det_worker = det_worker(
      dbline, 
      my_viewer.inqueue,
      myeventer.eve_worker.detectorqueue,
      worker_id,
      logger, 
      self.shared_mem.shm.name, 
    ) 
    
  def start(self):
    self.det_worker.start()
    self.viewer.inqueue.display_qinfo(info = self.type + ' ' + str(self.id) +  ' Spawn: ')
    self.viewer.inqueue.start_data_loop()
  
  async def stop(self):
    if self.det_worker.is_alive():
      await asyncio.to_thread(self.det_worker.inqueue.put, ('stop',))
      try:
        await asyncio.to_thread(self.det_worker.join, 5.0)
        self.shared_mem.shm.close() 
        self.shared_mem.shm.unlink()
      except RuntimeError:
        pass  # executor already shutting down
    
class det_worker(mp_process):
  def __init__(self, 
      dbline, 
      myviewer_queue, 
      myeventer_det_queue, 
      worker_id,
      logger, 
      shm_name, 
    ):
    super().__init__()
    self.type = 'D'
    self.id = dbline.id
    self.scaledown = None
    if dbline.cam_virtual_fps:
      self.dataqueue = c_buffer(
        #debug = 'Det' + str(self.id), 
      )
    else:  
      self.dataqueue = c_buffer(
        block_put = False, 
        #debug = 'Det' + str(self.id), 
      )
    self.myeventer_det_queue = myeventer_det_queue 
    self.tf_worker_id = worker_id
    self.viewer_queue = myviewer_queue
    self.inqueue = s_queue()
    self.shm_name = shm_name
    self.scaledown = 4

  def run(self):
    asyncio.run(self.async_runner()) 
    
  def sigint_handler(self, signal = None, frame = None ):
    self.got_sigint = True 

  async def in_queue_thread(self):
    try:
      while self.do_run:
        received = await asyncio.to_thread(self.inqueue.get)
        #print(f'***** DET Inqueue #{self.id}:', received) 
        if (received[0] == 'stop'):
          self.got_sigint = True
          self.do_run = False  
          if self.is_alive():
            if self._inq_task:
              self._inq_task.cancel()
              try:
                await self._inq_task
              except asyncio.CancelledError:
                pass
        else:
          self.logger.warning( 
              f'CA{self.id}: Unknown key in Inqueue: {received[0]}'
          ) 
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("in_queue_thread crashed: %s", fatal, exc_info=True)
    
  async def async_runner(self):
    try:
      self.logname = 'detector #'+str(self.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Detector #' + str(self.id))
      self.dbline = await stream.objects.aget(id = self.id)
      self.shared_mem = shared_mem(
        source_dict = _SH_MEM_ITEMS, 
        shape=(self.dbline.cam_yres, self.dbline.cam_xres, 3),
        shm_name=self.shm_name, 
      )
      self.got_sigint = False
      self._inq_task = None
      self.sl = speedlimit(period = 0.0)
      self.som = speedometer()
      self.do_run = True
      loop = asyncio.get_running_loop()
      loop.add_signal_handler(signal.SIGINT, self.sigint_handler)
      self._inq_task = asyncio.create_task(
        self.in_queue_thread(), 
        name = 'in_queue_thread', 
      )
      self.firstdetect = True
      self.ts_background = time()
      self.finished = True
      self.x_from_cam = -1
      self.y_from_cam = -1
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
      self.div_ts = 0.0
      self.div_old = 1.0
      self.fps_limit_old = -1
      #print(f'Launch: detector #{self.id}')
      while not self.got_sigint:
        frameline = await self.dataqueue.get(timeout = 2.0)
        if frameline:
          if frameline[1].shape[:2] != (self.y_from_cam, self.x_from_cam):
            self.y_from_cam, self.x_from_cam = frameline[1].shape[:2]
            self.scaledown = self.dbline.det_scaledown
            if not self.scaledown:
              if max(self.x_from_cam, self.y_from_cam) >= 2560:
                self.scaledown = 4
              elif max(self.x_from_cam, self.y_from_cam) >= 1280:
                self.scaledown = 2
              else:
                self.scaledown = 1
            if self.scaledown >= 4:
              self.linewidth = 3
            elif self.scaledown >= 2:
              self.linewidth = 4
            else:
              self.linewidth = 5 
            self.xres = self.x_from_cam // self.scaledown
            self.yres = self.y_from_cam // self.scaledown
            if self.scaledown > 1:
              self.buffer = await asyncio.to_thread(
                cv.resize, 
                frameline[1], 
                (self.xres, self.yres), 
                interpolation=cv.INTER_NEAREST,
              )
            else:
              self.buffer = frameline[1]
            self.background = np.float32(self.buffer)
            if not self.firstdetect:  
              self.background_mask = await asyncio.to_thread(
                cv.resize, 
                self.background_mask, 
                (self.xres, self.yres), 
                interpolation=cv.INTER_NEAREST,
              )
            self.shared_mem.write_1_meta('aoi_xdim', self.x_from_cam)
            self.shared_mem.write_1_meta('aoi_ydim', self.y_from_cam)
            self.shared_mem.write_1_meta('scaledown', self.scaledown)
          self.firstdetect = False
          frameline = await self.run_one(frameline)
        if frameline:
          if self.dbline.det_view and streams_redis.view_from_dev('D', self.id):
            await self.viewer_queue.put(frameline)
        await a_break_type(BR_SHORT)
      await self.dataqueue.stop()
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
    except Exception as fatal:
      self.logger.error(
        'Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("async_runner crashed: %s", fatal, exc_info=True)

  async def run_one(self, input): 
    if input[2] == 0.0:
      return(None)
    frametime = input[2]
    if ((new_time := time()) - self.div_ts >= 5.0 and 
        not self.dbline.cam_virtual_fps):  
      if (buffer_size := tf_workers_redis.get_buf_size_10(self.tf_worker_id)) < 2.5:
        divisor = 1.0  
      elif buffer_size < 5.0:
        divisor = 2.0   
      elif buffer_size < 10.0:
        divisor = 4.0  
      else:  
        divisor = 8.0  
      if self.fps_limit_old != (new_fps := self.shared_mem.read_1_meta('fps_limit')):
        if new_fps == 0:
          self.sl.period = 0.0
        else:
          self.sl.period = divisor / new_fps
        self.fps_limit_old = new_fps
      if divisor != self.div_old:
        self.div_old = divisor
        self.logger.warning(f'DE{self.id}: Fpm divisor = {divisor}')
      self.div_ts = new_time
    if self.got_sigint or not self.sl.greenlight(frametime):
      return(None)
    if self.run_lock and not self.dbline.cam_virtual_fps: 
      return(None)
    self.run_lock = True
    frame = input[1]
    frameall = frame
    if self.scaledown > 1:
      frame = await asyncio.to_thread(
        cv.resize, 
        frame, 
        (self.xres, self.yres), 
        interpolation=cv.INTER_NEAREST, 
      )
    if (self.shared_mem.read_1_meta('apply_mask') 
        and not self.shared_mem.read_1_meta('edit_active')): 
      if frame.shape[:2] == self.shared_mem.read_mask().shape[:2]:
        frame = await asyncio.to_thread(
          cv.bitwise_and, 
          frame, 
          self.shared_mem.read_mask(),
        )
    objectmaxsize = round(max(
      self.buffer.shape[0],
      self.buffer.shape[1],
    ) * self.shared_mem.read_1_meta('max_size'))
    buffer1 = await asyncio.to_thread(cv.absdiff, self.buffer, frame)
    buffer1 = await asyncio.to_thread(cv.split, buffer1)
    buffer2 = await asyncio.to_thread(cv.max, buffer1[0], buffer1[1])
    buffer1 = await asyncio.to_thread(cv.max, buffer2, buffer1[2])
    ret, buffer1 = await asyncio.to_thread(
      cv.threshold, 
      buffer1, 
      self.shared_mem.read_1_meta('threshold'), 
      255, 
      cv.THRESH_BINARY, 
     )
    if (erosion := self.shared_mem.read_1_meta('erosion')):
      kernel = np.ones((erosion*2 + 1,erosion*2 + 1),np.uint8)
      buffer2 = await asyncio.to_thread(cv.erode, buffer1, kernel, iterations =1)
    else:
      buffer2 = buffer1
    if (dilation := self.shared_mem.read_1_meta('dilation')):
      kernel = np.ones((dilation*2 + 1,dilation*2 + 1),np.uint8)
      buffer3 = await asyncio.to_thread(cv.dilate, buffer2, kernel, iterations =1)
    else:
      buffer3 = buffer2
    self.background_mask = 255 - buffer3
    buffer1 = await asyncio.to_thread(cv.cvtColor, buffer1, cv.COLOR_GRAY2BGR)
    buffer2 = await asyncio.to_thread(cv.cvtColor, buffer2, cv.COLOR_GRAY2BGR) 
    buffer4 = await asyncio.to_thread(cv.cvtColor, buffer3, cv.COLOR_GRAY2BGR)
    buffer1 = list(await asyncio.to_thread(cv.split, buffer1))
    buffer1[1] = buffer1[1] * 0
    buffer1 = await asyncio.to_thread(cv.merge, buffer1)
    buffer1 = await asyncio.to_thread(cv.addWeighted, buffer4, 0.2, buffer1, 1, 0)
    buffer1 = await asyncio.to_thread(cv.addWeighted, buffer1, 1, buffer2, 1, 0)
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
              retval, image, dummy, recta = await asyncio.to_thread(
                cv.floodFill, 
                buffer3, None,
                (x, y), 
                100, 
              )
              rectb = rect_atob(recta)
              rect_list.append(rectb)
              recta = rect_btoa(rectb)
    if rect_list:  
      rect_list = merge_rects(rect_list)  
      with self.myeventer_det_queue.multi_put_lock: 
        for rect in rect_list[:self.shared_mem.read_1_meta('max_rect')]:
          recta = rect_btoa(rect)
          await asyncio.to_thread(cv.rectangle, buffer1, recta, (200), self.linewidth)
          if ((recta[2]<=objectmaxsize) and (recta[3]<=objectmaxsize)):
            if not streams_redis.check_if_counts_zero('E', self.id):
              if self.scaledown > 1:
                rect = [item * self.scaledown for item in rect]
              aoi = np.copy(frameall[rect[2]:rect[3], rect[0]:rect[1]])
              await self.myeventer_det_queue.put((
                3, 
                aoi, 
                frametime, 
                rect, 
                (await asyncio.to_thread(cv.imencode, '.bmp', aoi))[1].tobytes(),
              ))  
          else:
            self.background = np.float32(frame)
        if not streams_redis.check_if_counts_zero('E', self.id):
          await self.myeventer_det_queue.put('stop')   
    self.shared_mem.read_1_meta('backgr_delay')
    if (b_delay := self.shared_mem.read_1_meta('backgr_delay')) == 0:
      self.buffer = frame
    else:
      if (time() >= (self.ts_background + b_delay)): 
        self.ts_background = time()
        await asyncio.to_thread(cv.accumulateWeighted, frame, self.background, 0.1)
      else:
        await asyncio.to_thread(
          cv.accumulateWeighted, 
          frame, 
          self.background, 
          0.5, 
          self.background_mask, 
        )
      self.buffer = np.uint8(self.background)
    fps = self.som.gettime()
    if fps:
      self.dbline.det_fpsactual = fps
      streams_redis.fps_to_dev(self.type, self.id, fps)
    self.run_lock = False
    if self.shared_mem.read_1_meta('edit_active'):
      return([3, frame, frametime])
    else:
      return([3, buffer1, frametime])

  async def stop(self):
    await self.dbline.asave(update_fields = ['det_fpsactual', ])
    await super().stop()

