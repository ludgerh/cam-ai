import sys
from logging import getLogger
from traceback import format_exc
from logging import getLogger
from time import sleep
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
        if self.myeventer.dbline.eve_mode_flag == 2:
          self.myeventer.run()
        if self.mydetector.dbline.det_mode_flag == 2:
          self.mydetector.run()
        self.mycam.run() 
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def stop(self):
    try:
      self.mycam.stop()
      self.mydetector.stop()
      self.myeventer.stop()
      self.logger.info('Finished Process '+self.logname+'...')
      self.logger.handlers.clear()
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()
