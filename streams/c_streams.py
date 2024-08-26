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

from logging import getLogger
from traceback import format_exc
from logging import getLogger
from tools.c_logger import log_ini
from tools.c_redis import myredis
from detectors.c_detectors import c_detector
from eventers.c_eventers import c_eventer
from .c_cams import c_cam

streams = {}

class c_stream():
  def __init__(self, dbline):
    self.dbline = dbline

  def start(self):
    try:
      self.logname = 'stream #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      log_ini(self.logger, self.logname)
      self.redis = myredis()
      self.redis.set('CAM-AI:KillStream:'+str(self.dbline.id), 0)
      self.redis.name_to_stream(self.dbline.id, self.dbline.name)
      if self.dbline.eve_mode_flag:
        self.myeventer = c_eventer(self.dbline, self.logger)
      if self.dbline.det_mode_flag:
        self.mydetector = c_detector(self.dbline, self.logger)
      self.mycam = c_cam(self.dbline, self.logger, self.mydetector)
      if self.dbline.eve_mode_flag:
        self.myeventer.parent = self.mydetector
        self.mydetector.myeventer = self.myeventer
      if self.dbline.det_mode_flag:
        self.mydetector.parent = self.mycam
      if self.dbline.cam_mode_flag == 2:
        self.mycam.run() 
        if self.mydetector.dbline.det_mode_flag == 2:
          self.mydetector.run()
        if self.myeventer.dbline.eve_mode_flag == 2:
          self.myeventer.run()
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def stop(self):
    self.redis.set('CAM-AI:KillStream:'+str(self.dbline.id), 1)
    self.mycam.stop()
    self.mydetector.stop()
    self.myeventer.stop()
    self.logger.info('Finished Process '+self.logname+'...')
    self.logger.handlers.clear()
