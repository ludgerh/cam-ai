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
import signal
import importlib.util
import sys
from pathlib import Path
from multiprocessing import Process as mp_process, SimpleQueue as s_queue
from os import environ
from logging import getLogger
from setproctitle import setproctitle
#from core.models import plugin as plugin_db
from streams.redis import my_redis as streams_redis
from tf_workers.redis import my_redis as tf_workers_redis
from tools.c_logger import alog_ini
from globals.c_globals import add_viewer
from tools.c_tools import (rect_btoa, merge_rects, c_buffer)
from tools.l_break import a_break_type, BR_SHORT
from viewers.c_viewers import c_viewer
from oneitem.shared_mem import shared_mem
from streams.models import stream

class c_detector():
  def __init__(self, dbline, myeventer, worker_id, logger, ):
    self.type = 'D'
    self.id = dbline.id
    add_viewer((my_viewer := c_viewer(self.type, self.id, logger,)))
    self.viewer = my_viewer
    self.viewer_queue = my_viewer.inqueue
    streams_redis.zero_to_dev(self.type, self.id)
    streams_redis.fps_to_dev(self.type, self.id, 0.0)
    plugin_line = dbline.det_plugin
    p = Path(plugin_line.path)
    spec = importlib.util.spec_from_file_location(p.stem, p)
    plugin_mod = importlib.util.module_from_spec(spec)
    sys.modules[p.stem] = plugin_mod  # ← verhindert Doppel-Imports
    spec.loader.exec_module(plugin_mod)
    self.plugin = plugin_mod.plugin()
    self.shared_mem = shared_mem(
      source_dict = self.plugin._SH_MEM_ITEMS, 
      shape = (dbline.cam_yres, dbline.cam_xres, 3), 
    )
    self.plugin.init_shared_mem(self.shared_mem, dbline)
    self.det_worker = det_worker(
      dbline, 
      my_viewer.inqueue,
      myeventer.eve_worker.detectorqueue,
      worker_id,
      logger, 
      self.shared_mem.shm.name, 
      plugin_line.path,
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
      except RuntimeError:
        pass  # executor already shutting down
      self.shared_mem.shm.close() 
      try:
        self.shared_mem.shm.unlink()
      except FileNotFoundError:
        pass
    
class det_worker(mp_process):
  def __init__(self, 
      dbline, 
      myviewer_queue, 
      myeventer_det_queue, 
      worker_id,
      logger, 
      shm_name, 
      plugin_path,
    ):
    super().__init__()
    self.type = 'D'
    self.id = dbline.id
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
    self.plugin_path = plugin_path
    self.logger = logger

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
      p = Path(self.plugin_path)
      spec = importlib.util.spec_from_file_location(p.stem, p)
      plugin_mod = importlib.util.module_from_spec(spec)
      sys.modules[p.stem] = plugin_mod
      spec.loader.exec_module(plugin_mod)
      self.plugin = plugin_mod.plugin()
      self.logger.info(f'**** Detector #{self.id} running Plugin: {self.plugin.name}')
      self.shared_mem = shared_mem(
        source_dict = self.plugin._SH_MEM_ITEMS, 
        shape=(self.dbline.cam_yres, self.dbline.cam_xres, 3),
        shm_name=self.shm_name, 
      )
      self.got_sigint = False
      loop = asyncio.get_running_loop()
      loop.add_signal_handler(signal.SIGINT, self.sigint_handler)
      self._inq_task = asyncio.create_task(
        self.in_queue_thread(), 
        name = 'in_queue_thread', 
      )
      self.do_run = True
      await self.plugin.async_init()
      self.x_from_cam = -1
      self.y_from_cam = -1
      self.run_lock = False
      environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
      if self.dbline.det_gpu_nr_cv == -1:
        environ["CUDA_VISIBLE_DEVICES"] = ''
      else:  
        environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.det_gpu_nr_cv)
      self.logger.info('**** Detector #' + str(self.id)+' running GPU #' 
        + str(self.dbline.det_gpu_nr_cv))
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
              self.last_frame = await asyncio.to_thread(
                cv.resize, 
                frameline[1], 
                (self.xres, self.yres), 
                interpolation=cv.INTER_NEAREST,
              )
            else:
              self.last_frame = frameline[1]
            self.background = np.float32(self.last_frame )
            self.shared_mem.write_1_meta('aoi_xdim', self.x_from_cam)
            self.shared_mem.write_1_meta('aoi_ydim', self.y_from_cam)
            self.shared_mem.write_1_meta('scaledown', self.scaledown)
          frameline = await self.run_one(frameline)
        if frameline:
          if self.dbline.det_view and streams_redis.view_from_dev('D', self.id):
            await self.viewer_queue.put(frameline)
        await a_break_type(BR_SHORT)
      await self.dataqueue.stop()
      self.logger.info('Finished Process '+self.logname+'...')
    except Exception as fatal:
      self.logger.error(
        'Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("async_runner crashed: %s", fatal, exc_info=True)

  async def run_one(self, frameline): 
    if frameline[2] == 0.0:
      return(None)
    frametime = frameline[2]
    greenlight = await self.plugin.check_time(
      frametime,
      self.shared_mem.read_1_meta('fps_limit'),
      self.dbline.cam_virtual_fps > 0.0,
      tf_workers_redis.get_buf_size_10(self.tf_worker_id),
      self.id,
      self.logger,
    )
    if self.got_sigint or not greenlight:
      return(None)
    if self.run_lock and not self.dbline.cam_virtual_fps: 
      return(None)
    self.run_lock = True
    frame = frameline[1]
    frameall = frame
    if self.scaledown > 1:
      frame = await asyncio.to_thread(
        cv.resize, 
        frame, 
        (self.xres, self.yres), 
        interpolation=cv.INTER_NEAREST, 
      )
    if self.shared_mem.read_1_meta('apply_mask'):
      mask = self.shared_mem.read_mask()
    else:
      mask = None  
    frame, self.last_frame, self.background, rect_list = await self.plugin.process_frame(
      frame = frame, 
      last_frame = self.last_frame, 
      background = self.background, 
      mask = mask, 
      edit_active = self.shared_mem.read_1_meta('edit_active'), 
      threshold = self.shared_mem.read_1_meta('threshold'), 
      erosion = self.shared_mem.read_1_meta('erosion'), 
      dilation = self.shared_mem.read_1_meta('dilation'), 
      backgr_delay = self.shared_mem.read_1_meta('backgr_delay'), 
      mode_code = self.shared_mem.read_1_meta('mode_code').decode('utf-8'), 
    )
    if len(rect_list):  
      objectmaxsize = round(max(
        self.last_frame .shape[0],
        self.last_frame .shape[1],
      ) * self.shared_mem.read_1_meta('max_size'))
      rect_list = merge_rects(rect_list)  
      with self.myeventer_det_queue.multi_put_lock: 
        for rect in rect_list[:self.shared_mem.read_1_meta('max_rect')]:
          recta = rect_btoa(rect)
          await asyncio.to_thread(cv.rectangle, frame, recta, (200), self.linewidth)
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
    fps = self.plugin.som.gettime()
    if fps:
      self.dbline.det_fpsactual = fps
      streams_redis.fps_to_dev(self.type, self.id, fps)
    self.run_lock = False
    return([3, frame, frametime])

  async def stop(self):
    await self.dbline.asave(update_fields = ['det_fpsactual', ])
    await super().stop()

