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

from os import nice
from pathlib import Path
from time import sleep
from multiprocessing import Process, Queue
from threading import Thread
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from logging import getLogger
from django.db import connections
from tools.l_tools import djconf
from tools.c_logger import log_ini
from eventers.models import event, event_frame
from tf_workers.models import school

datapath = djconf.getconfig('datapath', 'data/')
recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', datapath + 'schoolframes/'))

def sigint_handler(signal, frame):
  #print ('Devices: Interrupt is caught')
  pass
  
class c_cleanup():
  def __init__(self, *args, **kwargs):
    self.inqueue = Queue()

  def run(self):
    self.run_process = Process(target=self.runner)
    connections.close_all()
    self.run_process.start()

  def runner(self):
    #self.dbline = stream.objects.get(id=self.id)
    self.logname = 'cleanup'
    self.logger = getLogger(self.logname)
    log_ini(self.logger, self.logname)
    setproctitle('CAM-AI-Cleanup')
    Thread(target=self.in_queue_thread, name='InQueueThread').start()
    signal(SIGINT, sigint_handler)
    signal(SIGTERM, sigint_handler)
    signal(SIGHUP, sigint_handler)
    self.do_run = True
    nice(19)
    while self.do_run:
      # ***** cleaning up eventframes
      if self.do_run:
        for frameline in event_frame.objects.filter(deleted = True):
          self.logger.info('Cleanup: Deleting event_frame #' + str(frameline.id))
          del_path = schoolframespath / frameline.name
          if del_path.exists():
            del_path.unlink()
          frameline.delete()
          eventline = frameline.event
          eventline.numframes -= 1
          eventline.save(update_fields = ['numframes'])
      # ***** cleaning up events
      if self.do_run:
        for eventline in event.objects.filter(deleted = True):
          self.logger.info('Cleanup: Deleting event #' + str(eventline.id))
          framelines = event_frame.objects.filter(event__id = eventline.id)
          for frameline in framelines:
            del_path = schoolframespath / frameline.name
            if del_path.exists():
              del_path.unlink()
            frameline.delete()
          if (video_name := eventline.videoclip):
            for ext in ['.jpg', '.mp4', '.webm']:
              delpath = recordingspath / (video_name + ext)
              if delpath.exists():
                delpath.unlink() 
          eventline.delete()  
      for i in range(5): #later range(3600)
        if not self.do_run:
          break
        sleep(1.0)
    self.logger.info('Finished Process '+self.logname+'...')
    self.logger.handlers.clear()

  def in_queue_thread(self):
    while True:
      received = self.inqueue.get()
      if (received[0] == 'stop'):
        self.do_run = False
        break

  def stop(self):
    self.inqueue.put(('stop',))
    self.run_process.join()
    
my_cleanup = c_cleanup()    
