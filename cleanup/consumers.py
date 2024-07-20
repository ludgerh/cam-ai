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
#from tools.l_tools import djconf, displaybytes
from tools.c_redis import saferedis
#from tf_workers.models import school, worker
#from trainers.models import trainframe, trainer
#from eventers.models import event, event_frame
#from streams.models import stream as dbstream
#from users.models import userinfo
#from access.models import access_control
#from access.c_access import access

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
#datapath = djconf.getconfig('datapath', 'data/')
#recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
#schoolframespath = Path(djconf.getconfig('schoolframespath', datapath + 'schoolframes/'))

#long_brake = djconf.getconfigfloat('long_brake', 1.0)
#school_x_max = djconf.getconfigint('school_x_max', 500)
#school_y_max = djconf.getconfigint('school_y_max', 500)
  
#lock_dict = {}
#countdict = {}
#check_rec_lock = Lock()

#*****************************************************************************
# cleanup
#*****************************************************************************

def checkschool(myschool, mypipe):
  while True:
    try:
      myschooldir = school.objects.get(id=myschool).dir
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
  dbsetquery = trainframe.objects.filter(school=myschool)
  dbset = {item.name for item in dbsetquery}
  result = {
    'correct' : fileset & dbset,
    'missingdb' : fileset - dbset,
    'missingfiles' : dbset - fileset,
  }
  mypipe[OUT].send(result)
  
def fixmissingdb(myschool, set_to_delete):
  myschooldir = school.objects.get(id=myschool).dir
  for item in set_to_delete:
    (Path(myschooldir) / 'frames' / item).unlink()
  
def fixmissingfiles(myschool, set_to_delete):
  for item in set_to_delete:
    trainframe.objects.filter(name=item).delete()
    
def checkrecfiles(mypipe):
  filelist = list(recordingspath.iterdir())
  filelist_c = [item.name for item in filelist if (
    item.name[0] == 'C' 
    and item.suffix == '.mp4'
    and item.stat().st_mtime < (time() - 1800)
    and item.exists()
  )]
  fileset_jpg = {item.stem for item in filelist if (item.name[:2] == 'E_') 
    and (item.suffix == '.jpg')}
  fileset_mp4 = {item.stem for item in filelist if (item.name[:2] == 'E_') 
    and (item.suffix == '.mp4')}
  fileset_webm = {item.stem for item in filelist if (item.name[:2] == 'E_') 
    and (item.suffix == '.webm')}
  fileset = fileset_jpg & fileset_mp4
  fileset_all = fileset_jpg | fileset_mp4 | fileset_webm
  mydbset = event.objects.filter(videoclip__startswith='E_')
  while True:
    try:
      dbset = set()
      dbtimedict = {}
      for item in mydbset:
        dbset.add(item.videoclip)
        dbtimedict[item.videoclip] = item.start
      break
    except OperationalError:
      connection.close()
  correct = fileset & dbset
  missingdb = fileset_all - dbset
  missingfiles = dbset - fileset
  result = {
    'jpg' : len(fileset_jpg),
    'mp4' : len(fileset_mp4),
    'webm' : len(fileset_webm),
    'temp' : filelist_c,
    'correct' : len(correct),
    'missingdb' : missingdb,
    'missingfiles' : missingfiles,
    'dbtimedict' : dbtimedict,  
  }
  mypipe[OUT].send(result)
  
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
    
def checkevents(mypipe):
  eventframequery = event_frame.objects.all()
  while True:
    try:
      eventframeset = {item.event.id for item in eventframequery}
      break
    except OperationalError:
      connection.close()
  eventquery = event.objects.all()
  eventset = {item.id for item in eventquery}
  result = {
    'correct' : len(eventset & eventframeset),
    #'missingevents' : (eventframeset - eventset),
    'missingframes' : (eventset - eventframeset),
  }
  mypipe[OUT].send(result)
  
def fixmissingframes(list_to_delete):
  for item in list_to_delete:
    try:
      eventline = event.objects.get(id=item)
      if ((len(eventline.videoclip) < 3) 
          and (eventline.start.timestamp()  < (time() - 1800))):
        eventline.delete()
      else:
        event.objects.filter(id=item).update(numframes=0)
    except event.DoesNotExist:
      pass
    
def checkframes(mypipe):
  framefileset = {item.relative_to(schoolframespath).as_posix() 
    for item in schoolframespath.rglob('*.bmp')}
  framedbquery = event_frame.objects.all()
  while True:
    try:
      framedbset = {item.name for item in framedbquery}
      break
    except OperationalError:
      connection.close()
  framedbset = {item.name for item in framedbquery}
  result = {
    'correct' : len(framefileset & framedbset),
    'missingdblines' : framefileset - framedbset,
    'missingfiles' : framedbset - framefileset,
  }
  mypipe[OUT].send(result)
  
def fixmissingframesdb(list_to_delete):
  global countdict
  for item in list_to_delete:
    delpath = schoolframespath / item
    if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
      delpath.unlink()
      countpath = delpath.parent
      myindex = countpath.parent.name+'_'+countpath.name
      if myindex in countdict:
        countdict[myindex] -= 1
        mycount = countdict[myindex]
      else:
        mycount = len(list(countpath.iterdir()))
        countdict[myindex] = mycount
      if mycount == 0:
        countpath.rmdir()
  
def fixmissingframesfiles(list_to_delete):
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
    global lock_dict
    try:
      logger.debug('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

      if self.scope['user'].is_superuser:

        if params['command'] == 'checkschool':
          if not (params['school'] in lock_dict):
            lock_dict[params['school']] = Lock()
          with lock_dict[params['school']]:
            mypipe = Pipe()
            myproc = Process(target=checkschool, args=(params['school'], mypipe))
            myproc.start()
            result = mypipe[IN].recv()
            myproc.join()
          self.missingdbdict[params['school']] = result['missingdb']
          self.missingfilesdict[params['school']] = result['missingfiles']
          outlist['data'] = {
            'correct' : len(result['correct']),
            'missingdb' : len(result['missingdb']),
            'missingfiles' : len(result['missingfiles']),
          }
          logger.debug('--> ' + str(outlist))
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
          with check_rec_lock:
            mypipe = Pipe()
            myproc = Process(target=checkrecfiles, args=(mypipe, ))
            myproc.start()
            result = mypipe[IN].recv()
            myproc.join()
          self.fileset_c = result['temp']
          self.rec_missingdb = result['missingdb']
          self.rec_missingfiles = result['missingfiles']
          self.dbtimedict = result['dbtimedict']
          outlist['data'] = {
            'jpg' : result['jpg'],
            'mp4' : result['mp4'],
            'webm' : result['webm'],
            'temp' : len(self.fileset_c),
            'correct' : result['correct'],
            'missingdb' : len(self.rec_missingdb),
            'missingfiles' : len(self.rec_missingfiles),
          }
          logger.debug('--> ' + str(outlist))
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

        elif params['command'] == 'checkevents':
          with check_rec_lock:
            mypipe = Pipe()
            myproc = Process(target=checkevents, args=(mypipe, ))
            myproc.start()
            result = mypipe[IN].recv()
            myproc.join()
          #self.missingevents = result['missingevents'] 
          self.missingframes = result['missingframes'] 
          outlist['data'] = {
            'correct' : result['correct'],
            'missingevents' : 0,
            'missingframes' : len(self.missingframes),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingevents':	
          #not implemented. This case is not possible because of database logic
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingframes':		
          with check_rec_lock:
            myproc = Process(target=fixmissingframes, args=(self.missingframes, ))
            myproc.start()
            myproc.join()
            outlist['data'] = 'OK'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	

        elif params['command'] == 'checkframes':
          with check_rec_lock:
            mypipe = Pipe()
            myproc = Process(target=checkframes, args=(mypipe, ))
            myproc.start()
            result = mypipe[IN].recv()
            myproc.join()
          self.missingdblines = result['missingdblines']
          self.missingfiles = result['missingfiles']
          outlist['data'] = {
            'correct' : result['correct'],
            'missingdblines' : len(self.missingdblines),
            'missingfiles' : len(self.missingfiles),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingframesdb':	
          with check_rec_lock:
            myproc = Process(target=fixmissingframesdb, args=(self.missingdblines, ))
            myproc.start()
            myproc.join()
            outlist['data'] = 'OK'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	

        elif params['command'] == 'fixmissingframesfiles':	
          with check_rec_lock:
            myproc = Process(target=fixmissingframesfiles, args=(self.missingfiles, ))
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
