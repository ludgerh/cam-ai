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
from datetime import datetime
from multiprocessing import Process, Queue
from threading import Thread
from signal import signal, SIGINT, SIGTERM, SIGHUP
from traceback import format_exc
from setproctitle import setproctitle
from logging import getLogger
from datetime import datetime
from django.utils import timezone
from django.db import connections
from tools.l_tools import djconf, get_dir_size
from tools.l_smtp import smtp_send_mail
from tools.c_tools import check_db_connect
from tools.c_logger import log_ini
from tools.c_redis import saferedis
from eventers.models import event, event_frame
from trainers.models import trainframe
from tf_workers.models import school
from streams.models import stream
from trainers.models import model_type
from users.models import archive, userinfo
from .models import (status_line_event, status_line_video, status_line_school,
 files_to_delete)
from django.conf import settings

datapath = djconf.getconfig('datapath', 'data/')
recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', datapath + 'schoolframes/'))
archivepath = Path(djconf.getconfig('archivepath', datapath + 'archive/'))
schoolsdir = djconf.getconfig('schools_dir', datapath + 'schools/')

cleanup_interval = 5
health_check_interval = 3600

myredis = saferedis()

def sigint_handler(signal, frame):
  #print ('Devices: Interrupt is caught')
  pass
 
def clean_redis(name, idx=0): 
  mytag = 'cleanup:' + name + ':' + str(idx)
  myredis.delete(mytag)
   
def add_to_redis(name, idx, myvalue):
  myredis.set('cleanup:' + name + ':' + str(idx), myvalue)
   
def get_from_redis(name, idx):
  mytag = 'cleanup:' + name + ':' + str(idx)
  while (not myredis.exists(mytag)):
    sleep(djconf.getconfigfloat('short_brake', 0.1))
  return(int(myredis.get(mytag)))
   
def add_to_redis_queue(name, idx, myset):
  mytag = 'cleanup:' + name + ':' + str(idx)
  myredis.delete(mytag)
  for item in myset:
    myredis.lpush(mytag, item)
  
def get_from_redis_queue(name, idx):
  mytag = 'cleanup:' + name + ':' + str(idx)
  result = []  
  if myredis.exists(mytag):
    while (rline := myredis.rpop(mytag)):
      result.append(rline) 
  return(result)  
  
def len_from_redis_queue(name, idx):
  mytag = 'cleanup:' + name + ':' + str(idx)  
  if myredis.exists(mytag):
    return(myredis.llen(mytag))  
  else:
    return(0)  
  
class c_cleanup():
  def __init__(self, *args, **kwargs):
    self.inqueue = Queue()
    self.model_dims = {}
    for schoolline in school.objects.filter(active = True):
      myschooldir = schoolline.dir
      self.model_dims[schoolline.id] = []
      for item in model_type.objects.all():
        dim_code = str(item.x_in_default) + 'x' + str(item.y_in_default)
        if ((Path(myschooldir) / 'coded' / dim_code).exists()
            and any((Path(myschooldir) / 'coded' / dim_code).iterdir())):
          self.model_dims[schoolline.id].append(dim_code)

  def run(self):
    self.run_process = Process(target=self.runner)
    connections.close_all()
    self.run_process.start()

  def runner(self):
    try:
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
      clean_redis('videos_correct')
      clean_redis('videos_temp')
      clean_redis('videos_missingdb')
      clean_redis('videos_missingfiles')
      clean_redis('videos_mp4')
      clean_redis('videos_webm')
      clean_redis('videos_jpg')
      check_db_connect()
      for streamline in stream.objects.filter(active = True):
        clean_redis('events_frames_correct', streamline.id)
        clean_redis('events_frames_missingframes', streamline.id)
        clean_redis('eframes_correct', streamline.id)
        clean_redis('eframes_missingdb', streamline.id)
        clean_redis('eframes_missingfiles', streamline.id)
      for schoolline in school.objects.filter(active = True):
        clean_redis('schools_correct', schoolline.id)
        clean_redis('schools_missingdb', schoolline.id)
        clean_redis('schools_missingfiles', schoolline.id)
      while self.do_run:
        if self.do_run and time() - ts >= health_check_interval:
          self.health_check()
          ts =  time() 
        if False:
  # ***** cleaning up eventframes
          if self.do_run:
            check_db_connect()
            for frameline in event_frame.objects.filter(deleted = True):
              #self.logger.info('Cleanup: Deleting event_frame #' + str(frameline.id))
              del_path = schoolframespath / frameline.name
              if del_path.exists():
                del_path.unlink()
              frameline.delete()
              eventline = frameline.event
              eventline.numframes -= 1
              eventline.save(update_fields = ['numframes'])
  # ***** cleaning up events
          if self.do_run:
            check_db_connect()
            for eventline in event.objects.filter(deleted = True):
              #self.logger.info('Cleanup: Deleting event #' + str(eventline.id))
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
            check_db_connect()
            for frameline in trainframe.objects.filter(deleted = True):
              #self.logger.info('Cleanup: Deleting trainframe #' + str(frameline.id))
              myschooldir = Path(school.objects.get(id = frameline.school).dir)
              del_path = myschooldir / 'frames' / frameline.name
              if del_path.exists():
                del_path.unlink()
              frameline.delete()
  # ***** deleting files
          if self.do_run:
            check_db_connect()
            for fileline in files_to_delete.objects.all():
              delpath = Path(fileline.name)
              if delpath.exists():
                if (not fileline.min_age) or delpath.stat().st_mtime < time() - fileline.min_age:
                  #self.logger.info('Cleanup: Deleting file: ' + str(delpath))
                  delpath.unlink() 
              fileline.delete()
  # *****
        for i in range(cleanup_interval):
          if not self.do_run:
            break
          sleep(1.0)
      #self.logger.info('Finished Process '+self.logname+'...')
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
    timestamp = timezone.make_aware(datetime.now())
    check_db_connect()
    files_to_delete_list = [item.name for item in files_to_delete.objects.all()]
    print('+++++', files_to_delete_list, '+++++')
    for streamline in stream.objects.filter(active = True):
      my_status_events = status_line_event(made = timestamp, stream = streamline)
# ***** checking temp events
      check_db_connect()
      eventquery = event.objects.filter(deleted = False, camera = streamline.id, xmax__lte=0)
      events_temp = {item.id for item in eventquery if datetime.timestamp(item.start) < time() - 300.0}
      my_status_events.events_temp = len(events_temp)
      add_to_redis_queue('events_temp', streamline.id, events_temp)
# ***** checking eventframes vs events
      check_db_connect()
      eventframequery = event_frame.objects.filter(deleted = False, event__camera = streamline.id)
      eventframeset = {item.event.id for item in eventframequery}
      eventvideoquery = event.objects.filter(deleted = False, xmax__gt=0, camera = streamline.id).exclude(videoclip__exact = '') 
      eventvideoset = {item.id for item in eventvideoquery}   
      eventquery = event.objects.filter(deleted = False, xmax__gt=0, camera = streamline.id)
      eventset = {item.id for item in eventquery}
      events_frames_correct = eventset & (eventframeset | eventvideoset)
      my_status_events.events_frames_correct = len(events_frames_correct)
      add_to_redis('events_frames_correct', streamline.id, len(events_frames_correct))
      events_frames_missingframes = eventset - (eventframeset | eventvideoset)
      my_status_events.events_frames_missingframes = len(events_frames_missingframes)
      add_to_redis_queue('events_frames_missingframes', streamline.id, events_frames_missingframes)
# ***** checking eventframes vs files
      framefileset = {
        item.relative_to(schoolframespath).as_posix() 
        for item in (schoolframespath / str(streamline.id)).rglob('*.bmp')
      }
      check_db_connect()
      framedbquery = event_frame.objects.filter(deleted = False, event__camera = streamline.id)
      framedbset = {item.name for item in framedbquery}
      eframes_correct = framefileset & framedbset
      my_status_events.eframes_correct = len(eframes_correct)
      add_to_redis('eframes_correct', streamline.id, len(eframes_correct))
      eframes_missingdb = framefileset - framedbset
      my_status_events.eframes_missingdb = len(eframes_missingdb)
      add_to_redis_queue('eframes_missingdb', streamline.id, eframes_missingdb)
      eframes_missingfiles = framedbset - framefileset
      my_status_events.eframes_missingfiles = len(eframes_missingfiles)
      add_to_redis_queue('eframes_missingfiles', streamline.id, eframes_missingfiles)
      my_status_events.save()
# ***** checking videos vs files
    files_to_delete_set = {
      '/'.join(item.split('/')[1:]) 
      for item in files_to_delete_list 
      if item.startswith(recordingspath.as_posix() + '/')
    }
    my_status_videos = status_line_video(made = timestamp)
    filelist = list(recordingspath.iterdir())
    videos_temp = [item.name for item in filelist if (
      item.name[0] == 'C' 
      and item.suffix == '.mp4'
      and item.exists()
      and item.stat().st_mtime < (time() - 1800)
    )]
    my_status_videos.videos_temp = len(videos_temp)
    add_to_redis_queue('videos_temp', 0, videos_temp)
    videos_jpg = {item.stem for item in filelist if (item.name[:2] == 'E_') 
      and (item.suffix == '.jpg')
    } - files_to_delete_set
    my_status_videos.videos_jpg = len(videos_jpg)
    add_to_redis('videos_jpg', 0, len(videos_jpg))
    videos_mp4 = {item.stem for item in filelist if (item.name[:2] == 'E_') 
      and (item.suffix == '.mp4')
    } - files_to_delete_set
    my_status_videos.videos_mp4 = len(videos_mp4)
    add_to_redis('videos_mp4', 0, len(videos_mp4))
    videos_webm = {item.stem for item in filelist if (item.name[:2] == 'E_') 
      and (item.suffix == '.webm')
    } - files_to_delete_set
    my_status_videos.videos_webm = len(videos_webm)
    add_to_redis('videos_webm', 0, len(videos_webm))
    fileset = videos_jpg & videos_mp4
    fileset_all = videos_jpg | videos_mp4 | videos_webm
    check_db_connect()
    mydbset = event.objects.filter(deleted = False, videoclip__startswith = 'E_')
    dbset = set()
    dbtimedict = {}
    for item in mydbset:
      dbset.add(item.videoclip)
    videos_correct = fileset & dbset
    my_status_videos.videos_correct = len(videos_correct)
    add_to_redis('videos_correct', 0, len(videos_correct))
    videos_missingdb = fileset_all - dbset
    my_status_videos.videos_correct = len(videos_correct)
    videos_missingfiles = dbset - fileset
    my_status_videos.videos_missingfiles = len(videos_missingfiles)
    add_to_redis_queue('videos_temp', 0, videos_temp)
    add_to_redis_queue('videos_missingdb', 0, videos_missingdb)
    add_to_redis_queue('videos_missingfiles', 0, videos_missingfiles)
    my_status_videos.save()
# ***** checking trainframesdb vs files
    check_db_connect()
    for schoolline in school.objects.filter(active = True):
      my_status_schools = status_line_school(made = timestamp, school = schoolline)
      myschooldir = schoolline.dir
      files_to_delete_list_local = {
        item[len(myschooldir):]
        for item in files_to_delete_list 
        if item.startswith(myschooldir)
      }
      fileset = set()
      framespath = Path(myschooldir) / 'frames'
      if framespath.exists():
        for item in framespath.iterdir():
          if item.is_file() and item.suffix == '.bmp':
            if myschooldir + 'frames/' + item.as_posix() not in files_to_delete_list_local:
              fileset.add(item.stem)
          elif item.is_dir():
            subdir = item.name
            for item in (Path(myschooldir) / 'frames' / subdir).iterdir():
              if item.is_file() and item.suffix == '.bmp':
                if myschooldir + 'frames/' + subdir + '/' + item.as_posix() not in files_to_delete_list_local:
                  fileset.add(subdir+'/'+item.stem)
      for dim in self.model_dims[schoolline.id]:
        for item in (Path(myschooldir) / 'coded' / dim).iterdir():
          if item.is_file() and item.suffix == '.cod':
            if myschooldir + 'frames/' + dim + '/' + item.as_posix() not in files_to_delete_list_local:
              fileset.add(item.stem)
          elif item.is_dir():
            subdir = item.name
            for item in (Path(myschooldir) / 'coded' / dim / subdir).iterdir():
              if item.is_file() and item.suffix == '.cod':
                if myschooldir + 'frames/' + dim + '/' + subdir + '/' + item.as_posix() not in files_to_delete_list_local:
                  fileset.add(subdir+'/'+item.stem) 
      dbsetquery = trainframe.objects.filter(deleted = False, school=schoolline.id)
      dbset = {'.'.join(item.name.split('.')[:-1]) for item in dbsetquery}
      schools_correct = fileset & dbset
      my_status_schools.schools_correct = len(schools_correct)
      schools_missingdb = fileset - dbset
      my_status_schools.schools_missingdb = len(schools_missingdb)
      schools_missingfiles = dbset - fileset
      my_status_schools.schools_missingfiles = len(schools_missingfiles)
      add_to_redis('schools_correct', schoolline.id, len(schools_correct))
      add_to_redis_queue('schools_missingdb', schoolline.id, schools_missingdb)
      add_to_redis_queue('schools_missingfiles', schoolline.id, schools_missingfiles)
      my_status_schools.save()
    #self.logger.info('Cleanup: Getting stream file sizes') 
    check_db_connect()
    for streamline in stream.objects.all(): 
      result = get_dir_size(schoolframespath / str(streamline.id))
      for eventline in event.objects.filter(camera = streamline, double = False):
        if eventline.videoclip:
          for ext in ('.mp4', '.webm', '.jpg'):
            if (recordingspath / eventline.videoclip).with_suffix(ext).exists():
              result += (recordingspath / eventline.videoclip).with_suffix(ext).stat().st_size
      for archiveline in archive.objects.filter(stream = streamline):
        if archiveline.typecode == 0:
          filepath = archivepath / 'frames' / archiveline.name
          if filepath.exists():
            result += filepath.stat().st_size
        elif archiveline.typecode == 1:
          for ext in ('.mp4', '.webm', '.jpg'):
            filepath = (archivepath / 'videos' / archiveline.name).with_suffix(ext)
            if filepath.exists():
              result += filepath.stat().st_size
      streamline.storage_quota = result
      streamline.save(update_fields = ['storage_quota'])
    #self.logger.info('Cleanup: Getting school file sizes') 
    check_db_connect()
    for schoolline in school.objects.all():
      myschooldir = schoolline.dir
      result = get_dir_size(Path(myschooldir))
      schoolline.storage_quota = result
      schoolline.save(update_fields = ['storage_quota'])
    #self.logger.info('Cleanup: Getting users storage used') 
    check_db_connect()
    for userline in userinfo.objects.all():
      result = 0
      for streamline in stream.objects.filter(creator = userline.user):
        result += streamline.storage_quota
      for schoolline in school.objects.filter(creator = userline.user):
        result += schoolline.storage_quota
      userline.storage_used = result  
      if result < userline.storage_quota:  
        userline.mail_flag_quota100 = False
        if result < userline.storage_quota * 0.75:
          userline.mail_flag_quota75 = False
      if result > userline.storage_quota * 0.75:
        if not userline.mail_flag_quota75:
          print('Write 75')
          smtp_send_mail(
            'Notice: Your CAM-AI Storage is 75% Full',
            'Dear CAM-AI User, \n'
            'We want to inform you that your CAM-AI storage is now 75% full. \n'
            'To avoid any disruptions to your CAM-AI services, please consider managing your storage by deleting events. \n'
            'If you require an individual plan with additional storage, feel free to contact us at info@cam-ai.de \n'
            'Thank you for choosing CAM-AI. \n'
            'Best regards, \n'
            'The CAM-AI Team',
            'CAM-AI<' + settings.EMAIL_FROM + '>',
            userline.user.email,
            '<br>Dear CAM-AI User,<br>\n'
            '<br>We want to inform you that your CAM-AI storage is now 75% full.\n'
            'To avoid any disruptions to your CAM-AI services, please consider managing your storage by deleting events.<br>\n'
            '<br>If you require an individual plan with additional storage, feel free to contact us at info@cam-ai.de <br>\n'
            '<br>Thank you for choosing CAM-AI.<br>\n'
            '<br>Best regards,<br>\n'
            'The CAM-AI Team<br>\n'
            '<br><br><p style="color: lightgrey;">This email was sent automatically by the CAM-AI system.</p>',
            self.logger,
          )  
          userline.mail_flag_quota75 = True
        if result > userline.storage_quota:
          if not userline.mail_flag_quota100:
            print('Schreiben 100')
            smtp_send_mail(
              'Action Required: Your CAM-AI Storage is Full',
              'Dear CAM-AI User, \n'
              'We are reaching out to inform you that your CAM-AI storage is currently full. \n'
              'To ensure uninterrupted access to all CAM-AI features, please delete some events to free up space. \n'
              'If you require an individual plan with additional storage, feel free to contact us at info@cam-ai.de \n'
              'Thank you for choosing CAM-AI. \n'
              'Best regards, \n'
              'The CAM-AI Team',
              'CAM-AI<' + settings.EMAIL_FROM + '>',
              userline.user.email,
              '<br>Dear CAM-AI User,<br>\n'
              '<br>We are reaching out to inform you that your CAM-AI storage is currently full. \n'
              'To ensure uninterrupted access to all CAM-AI features, please delete some events to free up space.<br>\n'
              '<br>If you require an individual plan with additional storage, feel free to contact us at info@cam-ai.de <br>\n'
              '<br>Thank you for choosing CAM-AI.<br>\n'
              '<br>Best regards,<br>\n'
              'The CAM-AI Team<br>\n'
              '<br><br><p style="color: lightgrey;">This email was sent automatically by the CAM-AI system.</p>',
              self.logger,
            )  
            userline.mail_flag_quota100 = True
      userline.save(update_fields = ['storage_used', 'mail_flag_quota75', 'mail_flag_quota100',]) 
    self.logger.info('Cleanup: Finished health check')     

  def stop(self):
    self.inqueue.put(('stop',))
    self.run_process.join()
    
my_cleanup = c_cleanup()    
