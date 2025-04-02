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
 
import asyncio                
from logging import getLogger
from traceback import format_exc
from logging import getLogger
from multiprocessing import SimpleQueue
from asgiref.sync import sync_to_async
from tools.c_logger import log_ini
from globals.c_globals import add_viewer, add_viewable, tf_workers
from detectors.c_detectors import c_detector
from eventers.c_eventers import c_eventer
from .redis import my_redis
from .c_cams import c_cam
from .models import stream as dbstream

from globals.c_globals import viewables

class c_stream():
  def __init__(self, idx):
    self.id = idx
    
  async def run(self): 
    try:
      self.dbline = await dbstream.objects.aget(id = self.id)
      self.logname = 'stream #'+str(self.id)
      self.logger = getLogger(self.logname)
      log_ini(self.logger, self.logname)
      my_redis.set_killing_stream(self.id, False)
      if self.dbline.eve_mode_flag:
        eve_school = await sync_to_async(lambda: self.dbline.eve_school)() 
        tf_worker_db = await sync_to_async(lambda: eve_school.tf_worker)()
        my_worker = tf_workers[tf_worker_db.id] 
        self.myeventer = c_eventer(
          self.dbline, 
          my_worker.inqueue,
          my_worker.registerqueue,
          my_worker.id,
          self.logger,
        )
        add_viewable(self.myeventer)
      if self.dbline.det_mode_flag:
        self.mydetector = c_detector(
          self.dbline, 
          self.myeventer.detectorqueue,
          self.logger,
        )
        add_viewable(self.mydetector)
      self.mycam = c_cam(
        self.dbline, 
        self.mydetector.dataqueue,
        self.myeventer.dataqueue,
        self.myeventer.inqueue,
        self.logger,
      )
      add_viewable(self.mycam)
      if self.dbline.cam_mode_flag == 2:
        self.mycam.start() 
        await self.mycam.run_here()
        if self.dbline.det_mode_flag == 2:
          self.mydetector.start()
          await self.mydetector.run_here()
        if self.dbline.eve_mode_flag == 2:
          self.myeventer.start()
          await self.myeventer.run_here()
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc()) 

  async def stop(self):
    my_redis.set_killing_stream(self.dbline.id, True)
    await self.mycam.stop()
    self.mydetector.stop()
    self.myeventer.stop()
    self.logger.info('Finished Process '+self.logname+'...')
