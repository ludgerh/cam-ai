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
from time import sleep, time
from multiprocessing import Process, Queue
from threading import Thread
from signal import signal, SIGINT, SIGTERM, SIGHUP
from traceback import format_exc
from setproctitle import setproctitle
from logging import getLogger
from datetime import datetime
from django.utils import timezone
from django.db import connection, connections
from django.db.utils import OperationalError
from tools.l_tools import djconf
from tools.c_logger import log_ini
from tools.c_redis import saferedis
from eventers.models import event, event_frame
from trainers.models import trainframe
from tf_workers.models import school
from streams.models import stream
from .models import status_line, files_to_delete

datapath = djconf.getconfig('datapath', 'data/')
recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', datapath + 'schoolframes/'))
schoolsdir = djconf.getconfig('schools_dir', datapath + 'schools/')

cleanup_interval = 5
health_check_interval = 10 # later 3600

myredis = saferedis()

def sigint_handler(signal, frame):
  #print ('Devices: Interrupt is caught')
  pass
 
def clean_redis(name, idx=0): 
   myredis.delete('cleanup:' + name + ':' + str(idx))
   
def add_to_redis_queue(name, idx, myset):
  for item in myset:
    myredis.lpush('cleanup:' + name + ':' + str(idx), item)
    #print('cleanup:' + name + ':' + str(idx) + ':' + str(item))
  
  
class c_cleanup():
  def __init__(self, *args, **kwargs):
    self.inqueue = Queue()

  def run(self):
    self.run_process = Process(target=self.runner)
    connections.close_all()
    self.run_process.start()

  def runner(self):
    try:
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
      ts = 0.0
      clean_redis('video_missingdb')
      clean_redis('video_missingfiles')
      for streamline in stream.objects.filter(active = True):
        clean_redis('event_missing_frames', streamline.id)
        clean_redis('eframe_missing_db', streamline.id)
        clean_redis('eframe_missing_files', streamline.id)
      for schoolline in school.objects.filter(active = True):
        clean_redis('training_missing_db', schoolline.id)
        clean_redis('training_missing_files', schoolline.id)
      while self.do_run:
        if self.do_run and time() - ts >= health_check_interval:
          #self.health_check()
          ts =  time() 
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
        # ***** cleaning up trainframes
        if self.do_run:
          for frameline in trainframe.objects.filter(deleted = True):
            self.logger.info('Cleanup: Deleting trainframe #' + str(frameline.id))
            myschooldir = Path(school.objects.get(id = frameline.school).dir)
            del_path = myschooldir / 'frames' / frameline.name
            if del_path.exists():
              del_path.unlink()
            frameline.delete()
        for i in range(cleanup_interval):
          if not self.do_run:
            break
          sleep(1.0)
      self.logger.info('Finished Process '+self.logname+'...')
      self.logger.handlers.clear()
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())
      self.logger.handlers.clear()


  def in_queue_thread(self):
    try:
      while True:
        received = self.inqueue.get()
        if (received[0] == 'stop'):
          self.do_run = False
          break
    except:
      self.logger.error('Error in process: ' + self.logname + ' (in_queue_thread)')
      self.logger.error(format_exc())
      self.logger.handlers.clear()

        
  def health_check(self): 
    self.logger.info('Cleanup: Starting health check')
    my_status = status_line(made = timezone.make_aware(datetime.now()))
    # ***** checking eventframes vs events
    for streamline in stream.objects.filter(active = True):
      eventframequery = event_frame.objects.filter(deleted = False, event__camera = streamline.id)
      while True:
        try:
          eventframeset = {item.event.id for item in eventframequery}
          break
        except OperationalError:
          connection.close()  
      eventquery = event.objects.filter(deleted = False, xmax__gt=0, camera = streamline.id)
      eventset = {item.id for item in eventquery}
      event_frame_correct = len(eventset & eventframeset)
      missingframes = eventset - eventframeset
      add_to_redis_queue('event_missing_frames', streamline.id, missingframes)
      print('***', event_frame_correct, len(missingframes))
    # ***** checking eventframes vs files
    for streamline in stream.objects.filter(active = True):
      framefileset = {item.relative_to(schoolframespath).as_posix() 
        for item in (schoolframespath / str(streamline.id)).rglob('*.bmp')}
      framedbquery = event_frame.objects.filter(deleted = False, event__camera = streamline.id)
      while True:
        try:
          framedbset = {item.name for item in framedbquery}
          break
        except OperationalError:
          connection.close()
      framedbset = {item.name for item in framedbquery}
      eframe_file_correct = len(framefileset & framedbset)
      missingdblines = framefileset - framedbset
      missingfiles = framedbset - framefileset
      add_to_redis_queue('eframe_missing_db', streamline.id, missingdblines)
      add_to_redis_queue('eframe_missing_files', streamline.id, missingfiles)
      print('***', eframe_file_correct, len(missingdblines), len(missingfiles))
    # ***** checking videos vs files
    filelist = list(recordingspath.iterdir())
    video_temp = [item.name for item in filelist if (
      item.name[0] == 'C' 
      and item.suffix == '.mp4'
      and item.exists()
      and item.stat().st_mtime < (time() - 1800)
    )]
    video_jpg = {item.stem for item in filelist if (item.name[:2] == 'E_') 
      and (item.suffix == '.jpg')}
    video_mp4 = {item.stem for item in filelist if (item.name[:2] == 'E_') 
      and (item.suffix == '.mp4')}
    video_webm = {item.stem for item in filelist if (item.name[:2] == 'E_') 
      and (item.suffix == '.webm')}
    fileset = video_jpg & video_mp4
    fileset_all = video_jpg | video_mp4 | video_webm
    mydbset = event.objects.filter(deleted = False, videoclip__startswith = 'E_')
    while True:
      try:
        dbset = set()
        dbtimedict = {}
        for item in mydbset:
          dbset.add(item.videoclip)
        break
      except OperationalError:
        connection.close()
    video_correct = len(fileset & dbset)
    missingdb = fileset_all - dbset
    missingfiles = dbset - fileset
    add_to_redis_queue('video_temp', 0, video_temp)
    add_to_redis_queue('video_missingdb', 0, missingdb)
    add_to_redis_queue('video_missingfiles', 0, missingfiles)
    print('***', video_correct, len(video_temp), len(missingdb), len(missingfiles))
    # ***** checking trainframesdb vs files
    for schoolline in school.objects.filter(active = True):
      while True:
        try:
          myschooldir = schoolline.dir
          break
        except OperationalError:
          connection.close()
      fileset = set()
      for item in (Path(myschooldir) / 'frames').iterdir():
        if item.is_file():
          fileset.add(item.name)
        elif item.is_dir():
          subdir = item.name
          for item in (Path(myschooldir) / 'frames' / subdir).iterdir():
            fileset.add(subdir+'/'+item.name)
      dbsetquery = trainframe.objects.filter(deleted = False, school=schoolline.id)
      dbset = {item.name for item in dbsetquery}
      training_correct = len(fileset & dbset)
      missingdb = fileset - dbset
      missingfiles = dbset - fileset
      add_to_redis_queue('training_missing_db', schoolline.id, missingdb)
      add_to_redis_queue('training_missing_files', schoolline.id, missingfiles)
      my_status.save()
      print('***', training_correct, len(missingdb), len(missingfiles))

    self.logger.info('Cleanup: Finished health check')     

  def stop(self):
    self.inqueue.put(('stop',))
    self.run_process.join()
    
my_cleanup = c_cleanup()    
