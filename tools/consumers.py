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
import subprocess
import asyncio
import aiofiles
import aiofiles.os
import aiohttp
import aioshutil
import io
from asyncio import sleep as asleep
from pathlib import Path
from glob import glob
from os import makedirs, path as ospath, system as ossystem, getcwd, chdir, remove, nice
from shutil import copyfile, move, rmtree, copytree
from time import time, sleep
from random import randint
from setproctitle import setproctitle
from multiprocessing import Process, Pipe, Lock
from logging import getLogger
from traceback import format_exc
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
from camai.passwords import os_type, env_type 
from tools.l_tools import djconf, displaybytes
from tools.c_redis import myredis
from tf_workers.models import school, worker
from trainers.models import trainframe, trainer
from eventers.models import event, event_frame
from streams.models import stream as dbstream
from users.models import userinfo
from access.models import access_control
from access.c_access import access
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

logname = 'ws_tools'
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

class health(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      if self.scope['user'].is_superuser:
        self.missingdbdict= {}
        self.missingfilesdict = {}
        await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (health)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def receive(self, text_data):
    try:
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
    except:
      logger.error('Error in consumer: ' + logname + ' (health)')
      logger.error(format_exc())
      logger.handlers.clear()


#*****************************************************************************
# tools_async
#*****************************************************************************
        
def compress_backup(redis_key):
  setproctitle('CAM-AI-Backup-Compression')
  nice(19)
  basepath = getcwd() 
  chdir('..')
  if ospath.exists('temp/backup'):
    rmtree('temp/backup')
  makedirs('temp/backup') 
  redis.set(redis_key, 'Compressing Database...')
  cmd = 'mariadb-dump --password=' + db_password + ' '
  cmd += '--user=CAM-AI --host=localhost --all-databases '
  cmd += '> temp/backup/db.sql'
  subprocess.call(cmd, shell=True, executable='/bin/bash')
  with ZipFile('temp/backup/backup.zip', "w", ZIP_DEFLATED) as zip_file:
    zip_file.write('temp/backup/db.sql', 'db.sql')
  remove('temp/backup/db.sql')
  dirpath = Path(basepath + '/' + datapath)
  glob_list = []
  for item in dirpath.rglob("*"):
    if not (
      str(item.relative_to(dirpath)).startswith('static')
      or (str(item.relative_to(dirpath)).startswith(str(recordingspath.relative_to(Path(datapath)))+'/C'))
    ) : 
      glob_list.append(item)
  total =  len(glob_list)
  count = 0
  transmitted = 0
  with ZipFile('temp/backup/backup.zip', "a", ZIP_DEFLATED) as zip_file:
    for entry in glob_list:
      count += 1
      zip_file.write(entry, entry.relative_to(dirpath))
      percentage = (count / total * 100)
      if percentage >= transmitted + 0.1:
        redis.set(redis_key, str(round(percentage, 1)) + '% compressed')
        transmitted = percentage
  chdir(basepath)
  
class admin_tools_async(AsyncWebsocketConsumer):

  backup_proc_dict = {}

  async def connect(self):
    try:
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (admin_tools_async)')
      logger.error(format_exc())
      logger.handlers.clear()
    
  async def check_create_school_priv(self):
    if self.scope['user'].is_superuser:
      return(True)
    else:
      userinfo_obj = await userinfo.objects.aget(user=self.scope['user'])
      limit = userinfo_obj.allowed_schools
      schoolcount = await school.objects.filter(creator=self.scope['user']).acount()
      return(schoolcount < limit) 

  async def receive(self, text_data):
    try:
      logger.debug('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

#*****************************************************************************
# functions for the client
#*****************************************************************************

      if params['command'] == 'makeschool':
        if not await self.check_create_school_priv():
          await self.close()
        if using_websocket or remote_trainer:
          from aiohttp import ClientSession
        myschool = school()
        myschool.name = params['name']
        myschool.creator = self.scope['user']
        await myschool.asave()
        myworker = await worker.objects.aget(school__id=myschool.id)  
        schooldir = schoolsdir + 'model' + str(myschool.id) + '/'
        myschool.dir = schooldir
        await myschool.asave(update_fields=('dir', ))
        await aiofiles.os.makedirs(schooldir+'frames', exist_ok=True)
        await aiofiles.os.makedirs(schooldir+'model', exist_ok=True)
        if using_websocket or remote_trainer:
          async with ClientSession() as session:
            print('*****', myworker.wsserver + 'ws/schoolutil/')
            async with session.ws_connect(myworker.wsserver + 'ws/schoolutil/') as ws:
              outdict = {
                'code' : 'makeschool',
                'name' : 'CL' + str(myworker.wsid)+': ' + params['name'],
                'pass' : myworker.wspass,
                'user' : myworker.wsid,
              }
              await ws.send_str(json.dumps(outdict))
              message = await ws.receive()
              resultdict = json.loads(message.data)
        if not using_websocket:
          handle_src = await aiofiles.open(
            schoolsdir + 'model1/model/' + model_type + '.h5', mode='r')
          handle_dst = await aiofiles.open(
            schooldir + 'model/' + model_type + '.h5', mode='w')
          stat_src = await aiofiles.os.stat(
            schoolsdir + 'model1/model/' + model_type + '.h5')
          n_bytes = stat_src.st_size
          fd_src = handle_src.fileno()
          fd_dst = handle_dst.fileno()
          await aiofiles.os.sendfile(fd_dst, fd_src, 0, n_bytes)
        mytrainer = await trainer.objects.aget(school__id=myschool.id) 
        mytrainer.active=True    
        if using_websocket or remote_trainer:
          if resultdict['status'] == 'OK':
            myschool.e_school = resultdict['school']
            await myschool.asave(update_fields=('e_school', ))
            if remote_trainer:
              trainer_type = 2
            else:
              trainer_type = 3  
            mytrainer.t_type=trainer_type
            mytrainer.wsserver=myworker.wsserver
            mytrainer.wsname=myworker.wsname
            mytrainer.wspass=myworker.wspass
            await mytrainer.asave(update_fields=(
              't_type',
              'wsserver',
              'wsname',
              'wspass',
              'active',
            ))
            while redis.get_start_trainer_busy():
              sleep(long_brake)
            redis.set_start_trainer_busy(mytrainer.id)
        else:
          resultdict = {'status' : 'OK', }
          myschool.model_type = model_type
          await myschool.asave(update_fields=('model_type', ))
          mytrainer.t_type=1
          await mytrainer.asave(update_fields=('t_type', 'active', ))
        if resultdict['status'] == 'OK':
          if not self.scope['user'].is_superuser:
            myaccess = access_control()
            myaccess.vtype = 'S'
            myaccess.vid = myschool.id
            myaccess.u_g_nr = self.scope['user'].id
            myaccess.r_w = 'W'
            await myaccess.asave()
            await access.read_list_async()
        else:
          myschool.active = False
          await myschool.asave(update_fields=('active', ))
        outlist['data'] = resultdict
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

      elif params['command'] == 'linkworker':
        if not self.scope['user'].is_superuser:
          await self.close()
        from aiohttp import ClientSession
        async with ClientSession() as session:
          async with session.ws_connect(params['server'] + 'ws/aadmintools/') as ws:
            outdict = {
              'command' : 'linkserver',
              'user' : params['user'],
              'pass' : params['pass'],
            }
            await ws.send_str(json.dumps({
              'tracker' : 0, 
              'data' : outdict, 
            }))
            message = await ws.receive()
            resultdict = json.loads(message.data)
        if resultdict['data']['status'] == 'new': 
          myworker = await worker.objects.aget(id=params['workernr'])
          myworker.gpu_sim=-1
          myworker.use_websocket=using_websocket
          myworker.wsserver=params['server']
          myworker.wsname=resultdict['data']['user']
          myworker.wspass=params['pass']
          myworker.wsid=resultdict['data']['idx']
          await myworker.asave(update_fields=(
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
          async for item1 in myschools:
            mystreams = dbstream.objects.filter(eve_school=item1, active=True, )
            async for item2 in mystreams:
              streamlist.append(item2.id)
          for i in streamlist:
            while redis.get_start_stream_busy(): 
              sleep(long_brake)
            redis.set_start_stream_busy(i)
        outlist['data'] = resultdict['data']['status'] 
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
      elif params['command'] == 'checkserver':
        outlist['data'] = {} 
        if not self.scope['user'].is_superuser:
          await self.close() 
        from aiohttp import ClientSession
        from aiohttp.client_exceptions import ClientConnectorError
        try:
          async with ClientSession() as session:
            async with session.ws_connect(params['server'] + 'ws/aadmintools/') as ws:
              outdict = {
                'command' : 'getinfo',
              }
              await ws.send_str(json.dumps({
                'tracker' : 0, 
                'data' : outdict, 
              }))
              message = await ws.receive()
              resultdict = json.loads(message.data)
            outlist['data']['status'] = 'connect'
            outlist['data']['info'] = resultdict['data']
        except (ClientConnectorError, OSError):
          outlist['data']['status'] = 'noanswer'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

#*****************************************************************************
# functions for the server
#*****************************************************************************
      
      elif params['command'] == 'backup':
        if self.scope['user'].is_superuser:
          count = 0
          while count in self.backup_proc_dict:
            count += 1 
          redis_key = 'CAM-AI.backup.zip'+str(count)
          if redis.exists(redis_key):
            redis.delete(redis_key)
          self.backup_proc_dict[count] = Process(target=compress_backup, args=[redis_key])
          self.backup_proc_dict[count].start()
          while self.backup_proc_dict[count].is_alive():
            if redis.exists(redis_key):
              outlist['data'] = redis.get(redis_key).decode("utf-8")
              outlist['callback'] = True
              await self.send(json.dumps(outlist))	
              redis.delete(redis_key)
            else:  
              await asleep(long_brake) 
          outlist['data'] = 'OK'
          del outlist['callback']
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	
        else:
          await self.close()

      elif params['command'] == 'linkserver':
        outlist['data'] = {}
        try:
          myuser = await User.objects.aget(username = params['user'])
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
        await self.send(json.dumps(outlist))	
        
      elif params['command'] == 'getinfo':
        filename = textpath+'serverinfo.html'
        try:
          async with aiofiles.open(filename, mode='r', encoding='UTF-8') as f:
            result = await f.read()
        except FileNotFoundError:
          result = 'No Info: ' + textpath + 'serverinfo.html does not exist...'
        outlist['data'] = result
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
      if params['command'] == 'shutdown':
        if not self.scope['user'].is_superuser:
          await self.close()
        redis.set_shutdown_command(1)
        while redis.get_watch_status():
          await asleep(long_brake) 
        ossystem('sudo shutdown now')
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
      elif params['command'] == 'upgrade':
        if not self.scope['user'].is_superuser:
          await self.close()
        basepath = getcwd() 
        chdir('..')
        async with aiohttp.ClientSession() as session:
          async with session.get(params['url']) as result:
            response = await result.content.read()
        with ZipFile(io.BytesIO(response)) as z:
          z.extractall("temp/expanded")
        zipresult = glob('temp/expanded/ludgerh-cam-ai-*')[0]
        print(zipresult)
        if await aiofiles.os.path.exists('temp/backup'):
          await aioshutil.rmtree('temp/backup')
        await aioshutil.move(basepath, 'temp/backup') 
        await aioshutil.move(zipresult, basepath)
        await aioshutil.move('temp/backup/camai/passwords.py', basepath + '/camai/passwords.py')
        await aioshutil.move('temp/backup/eventers/c_alarm.py', basepath + '/eventers/c_alarm.py')
        await aioshutil.move('temp/backup/' + datapath, basepath + '/' + datapath)
        if env_type == 'venv':
          await aioshutil.move('temp/backup/env', basepath + '/env')
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
        p = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, executable='/bin/bash')
        output, _ = await p.communicate()
        for line in output.decode().split('\n'):
          logger.info(line);
        redis.set_shutdown_command(2)
        outlist['data'] = 'OK'
        logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        while redis.get_watch_status():
          await asleep(long_brake) 
    except:
      logger.error('Error in consumer: ' + logname + ' (admin_tools_async)')
      logger.error(format_exc())
      logger.handlers.clear()

