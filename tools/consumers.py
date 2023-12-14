# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
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

# /tools/consumers.py V0.9.15d 05.07.2023

import json
import subprocess
from asyncio import sleep as asleep
from pathlib import Path
from glob import glob
from os import makedirs, path as ospath, system as ossystem, getcwd, chdir, remove
from shutil import copyfile, move, rmtree, copytree
from time import time, sleep
from random import randint
from multiprocessing import Process, Pipe, Lock
from logging import getLogger
from ipaddress import ip_network, ip_address
from requests import get as rget
from zipfile import ZipFile, ZIP_DEFLATED
from django.contrib.auth.models import User
from django.db import connection
from django.db.utils import OperationalError
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from tools.c_logger import log_ini
from tools.djangodbasync import (getonelinedict, filterlinesdict, deletefilter, 
  updatefilter, savedbline, countfilter)
from camai.passwords import db_password 
try:  
  from camai.passwords import os_type, env_type 
except  ImportError: # can be removed when everybody is up to date
  os_type = 'raspi11'
  env_type = 'venv'  
from tools.l_tools import djconf, displaybytes
from tools.c_redis import myredis
from tools.c_tools import image_size, reduce_image
from tf_workers.models import school, worker
from trainers.models import trainframe, trainer
from eventers.models import event, event_frame
from streams.models import stream as dbstream
from users.models import userinfo
from access.models import access_control
from .health import totaldiscspace, freediscspace

OUT = 0
IN = 1

using_websocket = worker.objects.get(id = 1).use_websocket
remote_trainer = worker.objects.get(id=1).remote_trainer
if school.objects.count():
  model_type = school.objects.first().model_type
else:
  model_type = 'NotDefined'

redis = myredis()

logname = 'ws_toolsconsumers'
logger = getLogger(logname)
log_ini(logger, logname)
datapath = djconf.getconfig('datapath', 'data/')
recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', datapath + 'schoolframes/'))
textpath = djconf.getconfig('textpath', datapath + 'texts/')
if not ospath.exists(textpath):
  makedirs(textpath)
schoolsdir = djconf.getconfig('schools_dir', datapath + 'schools/')
basepath = getcwd() 
chdir('..')
if not ospath.exists('temp'):
  makedirs('temp')
chdir(basepath)

long_brake = djconf.getconfigfloat('long_brake', 1.0)
school_x_max = djconf.getconfigint('school_x_max', 500)
school_y_max = djconf.getconfigint('school_y_max', 500)
  
lock_dict = {}
countdict = {}
check_rec_lock = Lock()

#*****************************************************************************
# health
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
  eventframeset = {item.event.id for item in eventframequery}
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

class health(AsyncWebsocketConsumer):

  async def connect(self):
    if self.scope['user'].is_superuser:
      self.missingdbdict= {}
      self.missingfilesdict = {}
      await self.accept()

  async def receive(self, text_data):
    global lock_dict
    logger.debug('<-- ' + text_data)
    params = json.loads(text_data)['data']	
    outlist = {'tracker' : json.loads(text_data)['tracker']}	

    if params['command'] == 'getdiscinfo':
      outlist['data'] = {
        'total' : totaldiscspace,
        'free' : freediscspace,
        'totalstr' : displaybytes(totaldiscspace),
        'freestr' : displaybytes(freediscspace),
      }
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif self.scope['user'].is_superuser:

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


#*****************************************************************************
# dbcompress
#*****************************************************************************

def checkolddb(myschool, mypipe):
  myschooldir = school.objects.get(id=myschool).dir
  dbsetquery = trainframe.objects.filter(school=myschool)
  allset = {item.name for item in dbsetquery}
  oldset = {item.name for item in dbsetquery if ((item.name[1] != '/') and (item.name[2] != '/'))}
  bigset = set()
  i = dbsetquery.count()
  for item in dbsetquery:
    print(i, ':', item.name)
    filename = myschooldir + 'frames/' + item.name
    mysize = image_size(filename)
    if (mysize[0] > school_x_max) and (mysize[1] > school_y_max):
      bigset.add(item.name)
    i -= 1
  result = {
    'correct' : allset - oldset - bigset,
    'old' : oldset,
    'big' : bigset,
  }
  mypipe[OUT].send(result)
  
def fixbigimg(myschool, set_to_fix):
  myschooldir = school.objects.get(id=myschool).dir
  i = len(set_to_fix)
  for item in set_to_fix:
    print(i, ':', item)
    reduce_image(myschooldir + 'frames/' + item, None, school_x_max, school_y_max)
    i -= 1
  
def fixolddb(myschool, set_to_fix):
  myschooldir = school.objects.get(id=myschool).dir
  i = len(set_to_fix)
  for item in set_to_fix:
    print(i, ':', item)
    pathadd = str(randint(0,99))+'/'
    if not ospath.exists(myschooldir + 'frames/' + pathadd):
      makedirs(myschooldir + 'frames/' + pathadd)
    if ospath.exists(myschooldir + 'frames/' + item):
      move(myschooldir + 'frames/' + item, myschooldir + 'frames/' + pathadd)  
      try:
        frameline = trainframe.objects.get(name=item, school=myschool)
      except trainframe.MultipleObjectsReturned:
        frameline = trainframe.objects.filter(name=item, school=myschool).first()
      frameline.name = pathadd + frameline.name
      frameline.save(update_fields=("name", ))
    i -= 1
  
class dbcompress(AsyncWebsocketConsumer):

  async def connect(self):
    self.started = True
    if self.scope['user'].is_superuser:
      self.olddbddict = {}
      self.bigimgdict = {}
      await self.accept()
  
  async def disconnect(self, close_code):  
    self.started = False

  async def receive(self, text_data):
    global lock_dict
    logger.debug('<-- ' + text_data)
    params = json.loads(text_data)['data']	
    outlist = {'tracker' : json.loads(text_data)['tracker']}	

    if self.scope['user'].is_superuser:

      if params['command'] == 'checkolddb':
        if not (params['school'] in lock_dict):
          lock_dict[params['school']] = Lock()
        with lock_dict[params['school']]:
          mypipe = Pipe()
          myproc = Process(target=checkolddb, args=(params['school'], mypipe))
          myproc.start()
          while (not mypipe[IN].poll()):
            await asleep(1)
          result = mypipe[IN].recv()
          #while myproc.is_alive():
          #  await asleep(1)
          self.olddbddict[params['school']] = result['old']
          self.bigimgdict[params['school']] = result['big']
          outlist['data'] = {
            'correct' : len(result['correct']),
            'old' : len(result['old']),
            'big' : len(result['big']),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

      elif params['command'] == 'fixbigimg':	
        with lock_dict[params['school']]:
          myproc = Process(target=fixbigimg, args=(params['school'], self.bigimgdict[params['school']]))
          myproc.start()
          while myproc.is_alive():
            await asleep(1)
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

      elif params['command'] == 'fixolddb':	
        with lock_dict[params['school']]:
          myproc = Process(target=fixolddb, args=(params['school'], self.olddbddict[params['school']]))
          myproc.start()
          while myproc.is_alive():
            await asleep(1)
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

    else:
      await self.close()

#*****************************************************************************
# admintools
#*****************************************************************************

class admintools(WebsocketConsumer):

  def connect(self):
    self.accept()
    
  def check_create_school_priv(self):
    if self.scope['user'].is_superuser:
      return(True)
    else:
      limit = userinfo.objects.get(user=self.scope['user'].id).allowed_schools
      schoolcount = school.objects.filter(creator=self.scope['user'].id).count()
      return(schoolcount < limit)  

  def receive(self, text_data):
    logger.debug('<-- ' + text_data)
    params = json.loads(text_data)['data']	
    outlist = {'tracker' : json.loads(text_data)['tracker']}	

#*****************************************************************************
# functions for the client
#*****************************************************************************

    if params['command'] == 'makeschool':
      if not self.check_create_school_priv():
        self.close()
      if using_websocket or remote_trainer:
        from websocket import WebSocket
      myschool = school()
      myschool.name = params['name']
      myschool.creator = self.scope['user']
      myschool.save()
      myworker = myschool.tf_worker
      schooldir = schoolsdir + 'model' + str(myschool.id) + '/'
      try:
        makedirs(schooldir+'frames')
      except FileExistsError:
        logger.warning('Dir already exists: '+schooldir+'frames')
      try:
        makedirs(schooldir+'model')
      except FileExistsError:
        logger.warning('Dir already exists: '+schooldir+'model')
      if using_websocket or remote_trainer:
        ws = WebSocket()
        ws.connect(myworker.wsserver + 'ws/schoolutil/')
        outdict = {
          'code' : 'makeschool',
          'name' : 'CL' + str(myworker.wsid)+': ' + params['name'],
          'pass' : myworker.wspass,
          'user' : myworker.wsid,
        }
        ws.send(json.dumps(outdict), opcode=1) #1 = Text
        resultdict = json.loads(ws.recv())
        ws.close()
      if not using_websocket:
        copyfile(schoolsdir + 'model1/model/' + model_type + '.h5', 
          schooldir + 'model/' + model_type + '.h5')
      mytrainer = myschool.trainer
      mytrainer.active=True    
      if using_websocket or remote_trainer:
        if resultdict['status'] == 'OK':
          myschool.e_school = resultdict['school']
          myschool.save(update_fields=('e_school', ))
          if remote_trainer:
            trainer_type = 2
          else:
            trainer_type = 3  
          mytrainer.t_type=trainer_type
          mytrainer.wsserver=myworker.wsserver
          mytrainer.wsname=myworker.wsname
          mytrainer.wspass=myworker.wspass
          mytrainer.save(update_fields=(
            't_type',
            'wsserver',
            'wsname',
            'wspass',
            'active',
          ))
      else:
        resultdict = {'status' : 'OK', }
        myschool.model_type = model_type
        myschool.save(update_fields=('model_type', ))
        mytrainer.t_type=1
        mytrainer.save(update_fields=('t_type', 'active', ))
      while redis.get_start_trainer_busy():
        sleep(long_brake)
      redis.set_start_trainer_busy(myschool.trainer.id)
      if resultdict['status'] == 'OK':
        if not self.scope['user'].is_superuser:
          myaccess = access_control()
          myaccess.vtype = 'S'
          myaccess.vid = newschool.id
          myaccess.u_g_nr = self.scope['user'].id
          myaccess.r_w = 'W'
          myaccess.save()
      else:
        myschool.active = False
        myschool.save(update_fields=('active', ))
      outlist['data'] = resultdict
      logger.debug('--> ' + str(outlist))
      self.send(json.dumps(outlist))	

    elif params['command'] == 'linkworker':
      if not self.scope['user'].is_superuser:
        self.close()
      from websocket import WebSocket
      ws = WebSocket()
      ws.connect(params['server'] + 'ws/admintools/')
      outdict = {
        'command' : 'linkserver',
        'user' : params['user'],
        'pass' : params['pass'],
      }
      ws.send(json.dumps({
        'tracker' : 0, 
        'data' : outdict, 
      }), opcode=1) #1 = Text
      resultdict = json.loads(ws.recv())
      ws.close()
      if resultdict['data']['status'] == 'new': 
        myworker = worker.objects.get(id=params['workernr'])
        myworker.gpu_sim=-1
        myworker.use_websocket=using_websocket
        myworker.wsserver=params['server']
        myworker.wsname=resultdict['data']['user']
        myworker.wspass=params['pass']
        myworker.wsid=resultdict['data']['idx']
        myworker.save(update_fields=(
          'gpu_sim',
          'use_websocket',
          'wsserver',
          'wsname',
          'wspass',
          'wsid',
        ))
        while redis.get_start_worker_busy():
          sleep(long_brake)
        redis.set_start_worker_busy(params['workernr'])
        myschools = school.objects.filter(tf_worker=params['workernr'])
        streamlist = []
        for item1 in myschools:
          mystreams = dbstream.objects.filter(eve_school=item1)
          for item2 in mystreams:
            streamlist.append(item2.id)
        for i in streamlist:
          while redis.get_start_stream_busy(): 
            sleep(long_brake)
          redis.set_start_stream_busy(i)
      outlist['data'] = resultdict['data']['status'] 
      logger.debug('--> ' + str(outlist))
      self.send(json.dumps(outlist))	
      
    elif params['command'] == 'checkserver':
      outlist['data'] = {} 
      if not self.scope['user'].is_superuser:
        self.close() 
      from websocket import WebSocket
      from websocket._exceptions import WebSocketAddressException
      ws = WebSocket()
      try:
        ws.connect(params['server'] + 'ws/admintools/')
        outdict = {
          'command' : 'getinfo',
        }
        ws.send(json.dumps({
          'tracker' : 0, 
          'data' : outdict, 
        }), opcode=1) #1 = Text
        resultdict = json.loads(ws.recv())
        ws.close()
        outlist['data']['status'] = 'connect'
        outlist['data']['info'] = resultdict['data']
      except (WebSocketAddressException, OSError):
        outlist['data']['status'] = 'noanswer'
      logger.debug('--> ' + str(outlist))
      self.send(json.dumps(outlist))	

#*****************************************************************************
# functions for the server
#*****************************************************************************

    elif params['command'] == 'linkserver':
      outlist['data'] = {}
      try:
        myuser = User.objects.get(username = params['user'])
      except User.DoesNotExist:
        myuser = None
      if myuser:
        if myuser.check_password(params['pass']):
          outlist['data']['status'] = 'new'
          outlist['data']['idx'] = myuser.id
          outlist['data']['user'] = params['user']
        else:
          outlist['data']['status'] = 'noauth'
      else:
        outlist['data']['status'] = 'missing'
      logger.debug('--> ' + str(outlist))
      self.send(json.dumps(outlist))	
      
    elif params['command'] == 'getinfo':
      filename = textpath+'serverinfo.html'
      try:
        with open(filename, 'r', encoding='UTF-8') as f:
          result = f.read()
      except FileNotFoundError:
        result = 'No Info: ' + textpath + 'serverinfo.html does not exist...'
      outlist['data'] = result
      logger.debug('--> ' + str(outlist))
      self.send(json.dumps(outlist))	
      
    elif params['command'] == 'shutdown':
      if not self.scope['user'].is_superuser:
        self.close()
      redis.set_shutdown_command(1)
      while redis.get_watch_status():
        sleep(long_brake) 
      ossystem('sudo shutdown now')
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      self.send(json.dumps(outlist))	
      
    elif params['command'] == 'upgrade':
      if not self.scope['user'].is_superuser:
        self.close()
      basepath = getcwd() 
      chdir('..')
      response = rget(params['url'], stream=True)
      zip_path = "temp/cam-ai-upgrade.zip"
      with open(zip_path, mode="wb") as file:
        for chunk in response.iter_content(chunk_size=10 * 1024):
          file.write(chunk)    
      with ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall('.')  
      zipresult = glob('ludgerh-cam-ai-*')[0]
      remove(zip_path)
      if ospath.exists('temp/backup'):
        rmtree('temp/backup')
      move(basepath, 'temp/backup') 
      move(zipresult, basepath)
      move('temp/backup/camai/passwords.py', basepath + '/camai/passwords.py')
      move('temp/backup/eventers/c_alarm.py', basepath + '/eventers/c_alarm.py')
      move('temp/backup/' + datapath, basepath + '/' + datapath)
      if env_type == 'venv':
        move('temp/backup/env', basepath + '/env')
      chdir(basepath)
      if env_type == 'venv':
        cmd = 'source env/bin/activate; '
      else: #conda
        cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
        cmd += 'conda activate tf; '
      cmd += 'pip install --upgrade pip; '
      cmd += 'pip install -r requirements.' + os_type + '; '
      cmd += 'python manage.py migrate; '
      result = subprocess.check_output(cmd, shell=True, executable='/bin/bash').decode()
      for line in result.split('\n'):
        logger.info(line);
      redis.set_shutdown_command(2)
      while redis.get_watch_status():
        sleep(long_brake) 
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      self.send(json.dumps(outlist))	

    elif params['command'] == 'backup':
      if not self.scope['user'].is_superuser:
        self.close()
      basepath = getcwd() 
      chdir('..')
      if ospath.exists('temp/backup'):
        rmtree('temp/backup')
      makedirs('temp/backup') 
      outlist['data'] = 'Compressing Database...'
      outlist['callback'] = True
      self.send(json.dumps(outlist))	
      cmd = 'mariadb-dump --password=' + db_password + ' '
      cmd += '--user=CAM-AI --host=localhost --all-databases '
      cmd += '> temp/backup/db.sql'
      subprocess.call(cmd, shell=True, executable='/bin/bash')
      with ZipFile('temp/backup/backup.zip', "w", ZIP_DEFLATED) as zip_file:
        zip_file.write('temp/backup/db.sql', 'db.sql')
      remove('temp/backup/db.sql')
      dirpath = Path(basepath + '/' + datapath)
      total =  len(list(dirpath.rglob("*")))
      count = 0
      transmitted = 0
      with ZipFile('temp/backup/backup.zip', "a", ZIP_DEFLATED) as zip_file:
        for entry in dirpath.rglob("*"):
          count += 1
          zip_file.write(entry, entry.relative_to(dirpath))
          percentage = (count / total * 100)
          if percentage >= transmitted + 1.0:
            outlist['data'] = str(round(percentage)) + '% compressed'
            self.send(json.dumps(outlist))	
            transmitted = percentage
      chdir(basepath)
      outlist['data'] = 'OK'
      del outlist['callback']
      logger.info('--> ' + str(outlist))
      self.send(json.dumps(outlist))	
