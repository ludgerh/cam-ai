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

import sys
from time import sleep, time
from multiprocessing import Process, Queue
from threading import Thread
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from traceback import format_exc
from django.db import connections
from tools.l_tools import QueueUnknownKeyword, djconf
from tools.c_redis import myredis
from tools.c_tools import speedlimit, speedometer
from .models import stream

def sigint_handler(signal, frame):
  #print ('Devices: Interrupt is caught')
  pass

class c_device():

  def __init__(self, dbline, logger, detector=None):
    if detector: #Cams only
      self.mydetector = detector
    self.dbline = dbline
    self.id = dbline.id
    self.redis = myredis()
    self.inqueue = Queue()
    self.redis.zero_to_dev(self.type, self.dbline.id)
    self.redis.fps_to_dev(self.type, self.dbline.id, 0.0)
    self.logger = logger
    self.do_run = False
    self.viewer = None

  def run(self):
    if self.type == 'C':
      limit = 0
    elif self.type == 'D':
      limit = self.dbline.det_fpslimit
    elif self.type == 'E':
      limit = self.dbline.eve_fpslimit
    if limit == 0:
      self.period = 0.0
    else:
      self.period = 1.0 / limit
    self.sl = speedlimit()
    self.som = speedometer()
    self.do_run = True
    self.run_process = Process(target=self.runner)
    connections.close_all()
    self.run_process.start()

  def runner(self):
    self.dbline = stream.objects.get(id=self.id)
    Thread(target=self.in_queue_thread, name='InQueueThread').start()
    signal(SIGINT, sigint_handler)
    signal(SIGTERM, sigint_handler)
    signal(SIGHUP, sigint_handler)

  def in_queue_handler(self, received):
    if (received[0] == 'set_mask'):
      if self.viewer:
        mydrawpad = self.viewer.drawpad
        mydrawpad.ringlist = received[1]
        mydrawpad.make_screen()
        mydrawpad.mask_from_polygons()
    elif (received[0] == 'set_apply_mask'):
      if self.type == 'C':
        self.dbline.cam_apply_mask = received[1]
      elif self.type == 'D':
        self.dbline.det_apply_mask = received[1]
    else:
      return(False)
    return(True)

  def in_queue_thread(self):
    try:
      while True:
        received = self.inqueue.get()
        #print(self.type+str(self.dbline.id)+' in_queue_thread:', self.type, self.dbline.id, received)
        if (received[0] == 'stop'):
          print('?????', "self.do_run = False")
          self.do_run = False
          print('?????', "while not self.inqueue.empty():")
          while not self.inqueue.empty():
            print('Inqueue Loop')
            received = self.inqueue.get()
          print('?????', "break")
          break
        if not self.in_queue_handler(received):
          raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def add_view_count(self):
    self.redis.inc_view_dev(self.type, self.dbline.id)
    #print('Vie+', self.type, self.dbline.id, self.redis.view_from_dev(self.type, self.dbline.id))
    if self.type != 'C':
      self.parent.add_data_count()

  def take_view_count(self):
    self.redis.dec_view_dev(self.type, self.dbline.id)
    #print('Vie-', self.type, self.dbline.id, self.redis.view_from_dev(self.type, self.dbline.id))
    if self.type != 'C':
      self.parent.take_data_count()

  def add_record_count(self):
    if self.type == 'E':
      change = (self.redis.record_from_dev('E', self.dbline.id) == 0)
      self.redis.set_record_dev('E', self.dbline.id, 1)
    else:
      change = True
      self.redis.inc_record_dev(self.type, self.dbline.id)
    #print('Rec+', self.type, self.dbline.id, self.redis.record_from_dev(self.type, self.dbline.id))
    if (self.type != 'C') and change:
      self.parent.add_record_count()

  def take_record_count(self):
    if self.type == 'E':
      change = (self.redis.record_from_dev('E', self.dbline.id) == 1)
      self.redis.set_record_dev('E', self.dbline.id, 0)
    else:
      change = True
      self.redis.dec_record_dev(self.type, self.dbline.id)
    #print('Rec-', self.type, self.dbline.id, self.redis.record_from_dev(self.type, self.dbline.id))
    if (self.type != 'C') and change:
      self.parent.take_record_count()

  def add_data_count(self):
    if self.type == 'E':
      change = (self.redis.data_from_dev('E', self.dbline.id) == 0)
      self.redis.set_data_dev('E', self.dbline.id, 1)
    else:
      change = True
      self.redis.inc_data_dev(self.type, self.dbline.id)
    #print('Dat+', self.type, self.dbline.id, self.redis.data_from_dev(self.type, self.dbline.id))
    if (self.type != 'C') and change:
      self.parent.add_data_count()

  def take_data_count(self):
    if self.type == 'E':
      change = (self.redis.data_from_dev('E', self.dbline.id) == 1)
      self.redis.set_data_dev('E', self.dbline.id, 0)
    else:
      change = True
      self.redis.dec_data_dev(self.type, self.dbline.id)
    #print('Dat-', self.type, self.dbline.id, self.redis.data_from_dev(self.type, self.dbline.id))
    if (self.type != 'C') and change:
      self.parent.take_data_count()

  def stop(self):
    print('+++++', "self.viewer.stop()")
    if self.viewer:
      self.viewer.stop()
    print('+++++', "self.inqueue.put(('stop',))")
    self.inqueue.put(('stop',))
    print('+++++', "self.run_process.join()")
    self.run_process.join()
