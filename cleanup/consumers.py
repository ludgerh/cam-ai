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
#from time import time, sleep
#from random import randint
#from setproctitle import setproctitle
#from multiprocessing import Process, Pipe, Lock
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
from tools.c_redis import saferedis
#from tf_workers.models import school, worker
#from trainers.models import trainframe, trainer
from eventers.models import event, event_frame
#from streams.models import stream as dbstream
#from users.models import userinfo
#from access.models import access_control
#from access.c_access import access
from cleanup.c_cleanup import get_from_redis, get_from_redis_queue
from cleanup.models import files_to_delete

#OUT = 0
#IN = 1

#using_websocket = worker.objects.get(id = 1).use_websocket
#remote_trainer = worker.objects.get(id=1).remote_trainer
#if school.objects.count():
#  model_type = school.objects.first().model_type
#else:
#  model_type = 'NotDefined'

redis = saferedis()

logname = 'ws_cleanup'
logger = getLogger(logname)
log_ini(logger, logname)
datapath = djconf.getconfig('datapath', 'data/')
#recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
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
  
def fixmissingdb(myschool, set_to_delete):
  myschooldir = school.objects.get(id=myschool).dir
  for item in set_to_delete:
    (Path(myschooldir) / 'frames' / item).unlink()
  
def fixmissingfiles(myschool, set_to_delete):
  for item in set_to_delete:
    trainframe.objects.filter(name=item).delete()
  
def fixtemp_rec(list_to_delete):
  for item in list_to_delete:
    if (recordingspath / item).exists():
      (recordingspath / item).unlink()
  
def fixmissingdb_rec(list_to_delete):
  for item in list_to_delete:
    for ext in ['.jpg', '.mp4', '.webm']:
      delpath = recordingspath / (item+ext)
      if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
        delpath.unlink()
  
def fixmissingfiles_rec(list_to_delete, dbtimedict):
  for item in list_to_delete:
    if dbtimedict[item].timestamp()  < (time() - 1800):
      event.objects.filter(videoclip=item).update(videoclip='')
      for ext in ['.jpg', '.mp4', '.webm']:
        delpath = recordingspath / (item+ext)
        if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
          delpath.unlink()
  
def fixmissingframesfiles(list_to_delete): #Hier geht es weiter...
  mylength = len(list_to_delete)
  for item in list_to_delete:
    mylength -= 1
    try:
      frameline = event_frame.objects.get(name=item)
      if frameline.time.timestamp()  < (time() - 1800):
        frameline.delete()
    except event_frame.DoesNotExist:
      pass

class cleanup(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      if self.scope['user'].is_superuser:
        self.missingdbdict= {}
        self.missingfilesdict = {}
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
            'events_frames_correct' : get_from_redis('events_frames_correct', params['stream']),
            'events_frames_missingframes' : len(get_from_redis_queue('events_frames_missingframes', params['stream'])),
            'eframes_correct' : get_from_redis('eframes_correct', params['stream']),
            'eframes_missingdb' : len(get_from_redis_queue('eframes_missingdb', params['stream'])),
            'eframes_missingfiles' : len(get_from_redis_queue('eframes_missingfiles', params['stream'])),
          }
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_events_frames_missingframes':		
          list_to_delete = get_from_redis_queue('events_frames_missingframes', params['stream'])
          for item in list_to_delete:
            eventline = await event.objects.aget(id=int(item))
            eventline.deleted = True
            await eventline.asave(update_fields = ['deleted'])
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_eframes_missingdb':	
          list_to_delete = get_from_redis_queue('eframes_missingdb', params['stream'])
          for item in list_to_delete:
            del_line = files_to_delete(name = schoolframespath / item.decode())
            await del_line.asave()
          outlist['data'] = 'OK'
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	


        elif params['command'] == 'checkschool':
          outlist['data'] = {
            'schools_correct' : get_from_redis('schools_correct', params['school']),
            'schools_missingdb' : len(get_from_redis_queue('schools_missingdb', params['school'])),
            'schools_missingfiles' : len(get_from_redis_queue('schools_missingfiles', params['school'])),
          }
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingdb':	
          with lock_dict[params['school']]:
            myproc = Process(target=fixmissingdb, args=(params['school'], self.missingdbdict[params['school']]))
            myproc.start()
            myproc.join()
            outlist['data'] = 'OK'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingfiles':	
          with lock_dict[params['school']]:
            myproc = Process(target=fixmissingfiles, args=(params['school'], self.missingfilesdict[params['school']]))
            myproc.start()
            myproc.join()
            outlist['data'] = 'OK'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	

        elif params['command'] == 'checkrecfiles':
          outlist['data'] = {
            'videos_correct' : get_from_redis('videos_correct', 0),
            'videos_missingdb' : len(get_from_redis_queue('videos_missingdb', 0)),
            'videos_missingfiles' : len(get_from_redis_queue('videos_missingfiles', 0)),
            'videos_temp' : len(get_from_redis_queue('videos_temp', 0)),
            'videos_mp4' : get_from_redis('videos_mp4', 0),
            'videos_webm' : get_from_redis('videos_webm', 0),
            'videos_jpg' : get_from_redis('videos_jpg', 0),
          }
          logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixtemp_rec':	
          with check_rec_lock:
            myproc = Process(target=fixtemp_rec, args=(self.fileset_c, ))
            myproc.start()
            myproc.join()
            outlist['data'] = 'OK'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingdb_rec':	
          with check_rec_lock:
            myproc = Process(target=fixmissingdb_rec, args=(self.rec_missingdb, ))
            myproc.start()
            myproc.join()
            outlist['data'] = 'OK'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingfiles_rec':	
          with check_rec_lock:
            myproc = Process(target=fixmissingfiles_rec, args=(self.rec_missingfiles, self.dbtimedict, ))
            myproc.start()
            myproc.join()
            outlist['data'] = 'OK'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            
      else:
        await self.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (cleanup)')
      logger.error(format_exc())
      logger.handlers.clear()
