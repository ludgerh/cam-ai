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

import json
from pathlib import Path
#from glob import glob
#from shutil import copyfile, move, rmtree, copytree
from time import sleep
#from random import randint
#from setproctitle import setproctitle
#from multiprocessing import Process, Pipe, Lock
from threading import Lock as t_lock
from logging import getLogger
from traceback import format_exc
#from ipaddress import ip_network, ip_address
#from requests import get as rget
#from zipfile import ZipFile, ZIP_DEFLATED
#from django.contrib.auth.models import User
#from django.db import connection
#from django.db.utils import OperationalError
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini
#from tools.djangodbasync import (getonelinedict, filterlinesdict, deletefilter, 
#  updatefilter, savedbline, countfilter)
#from camai.passwords import db_password 
#from camai.passwords import os_type, env_type 
from tools.l_tools import djconf
from tf_workers.models import school
from trainers.models import trainframe
from eventers.models import event, event_frame
#from streams.models import stream as dbstream
#from users.models import userinfo
#from access.models import access_control
#from access.c_access import access
from cleanup.c_cleanup import get_from_redis, get_from_redis_queue, len_from_redis_queue
from cleanup.models import files_to_delete

#OUT = 0
#IN = 1

#using_websocket = worker.objects.get(id = 1).use_websocket
#remote_trainer = worker.objects.get(id=1).remote_trainer
#if school.objects.count():
#  model_type = school.objects.first().model_type
#else:
#  model_type = 'NotDefined'

logname = 'ws_cleanup'
logger = getLogger(logname)
log_ini(logger, logname)
datapath = djconf.getconfig('datapath', 'data/')
recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', datapath + 'schoolframes/'))

#long_brake = djconf.getconfigfloat('long_brake', 1.0)
#school_x_max = djconf.getconfigint('school_x_max', 500)
#school_y_max = djconf.getconfigint('school_y_max', 500)
  
#lock_dict = {}
#countdict = {}
#check_rec_lock = Lock()

#*****************************************************************************
# cleanup
#*****************************************************************************

class cleanup(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      if self.scope['user'].is_superuser:
        self.missingdbdict= {}
        self.missingfilesdict = {}
        self.counter_lock = t_lock()
        await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (cleanup)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def receive(self, text_data):
    try:
      logger.info('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

      if self.scope['user'].is_superuser:

        if params['command'] == 'checkevents':
          outlist['data'] = {
            'events_temp' : len_from_redis_queue('events_temp', params['stream']),
            'events_frames_correct' : get_from_redis('events_frames_correct', params['stream']),
            'events_frames_missingframes' : len_from_redis_queue('events_frames_missingframes', params['stream']),
            'eframes_correct' : get_from_redis('eframes_correct', params['stream']),
            'eframes_missingdb' : len_from_redis_queue('eframes_missingdb', params['stream']),
            'eframes_missingfiles' : len_from_redis_queue('eframes_missingfiles', params['stream']),
          }
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_events_temp':		
          list_to_delete = get_from_redis_queue('events_temp', params['stream'])
          counter = len(list_to_delete)
          for item in list_to_delete:
            eventline = await event.objects.aget(id=int(item))
            eventline.deleted = True
            await eventline.asave(update_fields = ['deleted'])
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_events_frames_missingframes':		
          list_to_delete = get_from_redis_queue('events_frames_missingframes', params['stream'])
          counter = len(list_to_delete)
          for item in list_to_delete:
            eventline = await event.objects.aget(id=int(item))
            eventline.deleted = True
            await eventline.asave(update_fields = ['deleted'])
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_eframes_missingdb':	
          print('*****')
          list_to_delete = get_from_redis_queue('eframes_missingdb', params['stream'])
          print(list_to_delete)
          counter = len(list_to_delete)
          for item in list_to_delete:
            del_line = files_to_delete(name = schoolframespath / item.decode(), min_age = 300)
            await del_line.asave()
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_eframes_missingfiles':	
          list_to_delete = get_from_redis_queue('eframes_missingfiles', params['stream'])
          counter = len(list_to_delete)
          for item in list_to_delete:
            eframe_line = await event_frame.objects.aget(name = item.decode())
            eframe_line.deleted = True
            await eframe_line.asave(update_fields = ['deleted'])
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'checkschool':
          outlist['data'] = {
            'schools_correct' : get_from_redis('schools_correct', params['school']),
            'schools_missingdb' : len_from_redis_queue('schools_missingdb', params['school']),
            'schools_missingfiles' : len_from_redis_queue('schools_missingfiles', params['school']),
          }
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_schools_missingdb':	
          school_line = await school.objects.aget(id=params['school'])
          myschooldir = school_line.dir
          list_to_delete = get_from_redis_queue('schools_missingdb', params['school'])
          counter = len(list_to_delete)
          for item in list_to_delete:
            del_line = files_to_delete(name = school_line.dir + '/frames/' + item.decode(), min_age = 300)
            await del_line.asave()
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_schools_missingfiles':	
          list_to_delete = get_from_redis_queue('schools_missingfiles', params['school'])
          counter = len(list_to_delete)
          for item in list_to_delete:
            frame_line = await trainframe.objects.aget(name = item.decode())
            frame_line.deleted = True
            await frame_line.asave(update_fields = ['deleted'])
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'checkrecfiles':
          outlist['data'] = {
            'videos_correct' : get_from_redis('videos_correct', 0),
            'videos_missingdb' : len_from_redis_queue('videos_missingdb', 0),
            'videos_missingfiles' : len_from_redis_queue('videos_missingfiles', 0),
            'videos_temp' : len_from_redis_queue('videos_temp', 0),
            'videos_mp4' : get_from_redis('videos_mp4', 0),
            'videos_webm' : get_from_redis('videos_webm', 0),
            'videos_jpg' : get_from_redis('videos_jpg', 0),
          }
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_videos_temp':	
          list_to_delete = get_from_redis_queue('videos_temp', 0)
          counter = len(list_to_delete)
          for item in list_to_delete:
            del_line = files_to_delete(name = recordingspath / item.decode())
            await del_line.asave()
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_videos_missingdb':	
          list_to_delete = get_from_redis_queue('videos_missingdb', 0)
          counter = len(list_to_delete)
          for item in list_to_delete:
            for ext in ['.jpg', '.mp4', '.webm']:
              delpath = recordingspath / (item.decode() + ext)
              del_line = files_to_delete(name = delpath, min_age = 300)
              await del_line.asave()
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_videos_missingfiles':	
          list_to_delete = get_from_redis_queue('videos_missingfiles', 0)
          counter = len(list_to_delete)
          print(list_to_delete)
          for item in list_to_delete:
            eventlines = event.objects.filter(videoclip=item.decode())
            async for eventline in eventlines:
              eventline.videoclip=''
              await eventline.asave(update_fields = ['videoclip'])
            for ext in ['.jpg', '.mp4', '.webm']:
              delpath = recordingspath / (item.decode() + ext)
              del_line = files_to_delete(name = delpath, min_age = 300)
              await del_line.asave()
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	
            
      else:
        await self.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (cleanup)')
      logger.error(format_exc())
      logger.handlers.clear()
