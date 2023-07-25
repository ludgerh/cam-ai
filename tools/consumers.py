# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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
from pathlib import Path
from os import makedirs, path as ospath
from shutil import copyfile
from time import time, sleep
from json import loads, dumps
from subprocess import Popen, PIPE
from multiprocessing import Process, Pipe, Lock
from logging import getLogger
from traceback import format_exc
from ipaddress import ip_network, ip_address
from socket import (socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, gethostbyaddr, herror, 
  gaierror, inet_aton)
from passlib.hash import phpass
from django.contrib.auth.models import User
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from camai.passwords import db_password
from tools.c_logger import log_ini
from tools.djangodbasync import (getonelinedict, filterlinesdict, deletefilter, 
  updatefilter, savedbline, getexists, createuser, countfilter)
from tools.l_tools import djconf, displaybytes
from tf_workers.models import school, worker
from tools.c_redis import myredis
from trainers.models import trainframe, trainer
from eventers.models import event, event_frame
from streams.c_streams import streams, c_stream
from streams.c_camera import c_camera
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
recordingspath = Path(djconf.getconfig('recordingspath', 'data/recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', 'data/schoolframes/'))
textpath = djconf.getconfig('textpath', 'data/texts/')
if not ospath.exists(textpath):
  makedirs(textpath)
schoolsdir = djconf.getconfig('schools_dir', 'data/schools/')
long_brake = djconf.getconfigfloat('long_brake', 1.0)

s = socket(AF_INET, SOCK_DGRAM)
subnetmask = '255.255.255.0'
try:
  s.connect(('10.255.255.255', 1))
  my_ip = s.getsockname()[0]
except Exception:
  my_ip = '127.0.0.1'
finally:
  s.close()
my_net = ip_network(my_ip+'/'+subnetmask, strict=False)
my_ip = ip_address(my_ip)

def is_valid_IP_Address(ip_str):
  result = True
  try:
    inet_aton(ip_str)
  except OSError:
    result = False
  return result
  
outPipe, inPipe = Pipe()  

proc_dict = {}
pipe_dict = {}
lock_dict = {}


countdict = {}

def checkschool(myschool):
  myschooldir = school.objects.get(id=myschool).dir
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
  pipe_dict[myschool][OUT].send(result)
  
def fixmissingdb(myschool):
  myschooldir = school.objects.get(id=myschool).dir
  set_to_delete = pipe_dict[myschool][IN].recv()
  for item in set_to_delete:
    (Path(myschooldir) / 'frames' / item).unlink()
  
def fixmissingfiles(myschool):
  set_to_delete = pipe_dict[myschool][IN].recv()
  for item in set_to_delete:
    trainframe.objects.get(name=item).delete()
    
def checkrecordings():
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
  dbset = set()
  dbtimedict = {}
  for item in mydbset:
    dbset.add(item.videoclip)
    dbtimedict[item.videoclip] = item.start
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
  check_rec_pipe[OUT].send(result)
  
def fixtemp_rec():
  list_to_delete = check_rec_pipe[IN].recv()
  for item in list_to_delete:
    if (recordingspath / item).exists():
      (recordingspath / item).unlink()
  
def fixmissingdb_rec():
  list_to_delete = check_rec_pipe[IN].recv()
  for item in list_to_delete:
    for ext in ['.jpg', '.mp4', '.webm']:
      delpath = recordingspath / (item+ext)
      if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
        delpath.unlink()
  
def fixmissingfiles_rec():
  list_to_delete = check_rec_pipe[IN].recv()
  dbtimedict = check_rec_pipe[IN].recv()
  for item in list_to_delete:
    if dbtimedict[item].timestamp()  < (time() - 1800):
      event.objects.filter(videoclip=item).update(videoclip='')
      for ext in ['.jpg', '.mp4', '.webm']:
        delpath = recordingspath / (item+ext)
        if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
          delpath.unlink()
  
check_rec_proc = None
check_rec_pipe = None
check_rec_lock = Lock()
    
def checkevents():
  eventframequery = event_frame.objects.all()
  eventframeset = {item.event.id for item in eventframequery}
  eventquery = event.objects.all()
  eventset = {item.id for item in eventquery}
  result = {
    'correct' : len(eventset & eventframeset),
    #'missingevents' : (eventframeset - eventset),
    'missingframes' : (eventset - eventframeset),
  }
  check_rec_pipe[OUT].send(result)
  
def fixmissingframes():
  list_to_delete = check_rec_pipe[IN].recv()
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
    
def checkframes():
  framefileset = {item.relative_to(schoolframespath).as_posix() 
    for item in schoolframespath.rglob('*.bmp')}
  framedbquery = event_frame.objects.all()
  framedbset = {item.name for item in framedbquery}
  result = {
    'correct' : len(framefileset & framedbset),
    'missingdblines' : framefileset - framedbset,
    'missingfiles' : framedbset - framefileset,
  }
  check_rec_pipe[OUT].send(result)
  
def fixmissingframesdb():
  global countdict
  list_to_delete = check_rec_pipe[IN].recv()
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
        pass
  
def fixmissingframesfiles():
  list_to_delete = check_rec_pipe[IN].recv()
  for item in list_to_delete:
    try:
      frameline = event_frame.objects.get(name=item)
      if frameline.time.timestamp()  < (time() - 1800):
        frameline.delete()
    except event_frame.DoesNotExist:
      pass

#*****************************************************************************
# health
#*****************************************************************************

class health(AsyncWebsocketConsumer):

  async def connect(self):
    if self.scope['user'].is_superuser:
      self.missingdbdict= {}
      self.missingfilesdict = {}
      await self.accept()

  async def receive(self, text_data):
    global check_rec_proc
    global check_rec_pipe
    logger.debug('<-- ' + text_data)
    params = loads(text_data)['data']	
    outlist = {'tracker' : loads(text_data)['tracker']}	

    if params['command'] == 'getdiscinfo':
      outlist['data'] = {
        'total' : totaldiscspace,
        'free' : freediscspace,
        'totalstr' : displaybytes(totaldiscspace),
        'freestr' : displaybytes(freediscspace),
      }
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif self.scope['user'].is_superuser:

      if params['command'] == 'checkschool':
        if not (params['school'] in lock_dict):
          lock_dict[params['school']] = Lock()
        with lock_dict[params['school']]:
          proc_dict[params['school']] = Process(target=checkschool, args=(params['school'],))
          pipe_dict[params['school']] = Pipe()
          proc_dict[params['school']].start()
          result = pipe_dict[params['school']][IN].recv()
          proc_dict[params['school']].join()
          del pipe_dict[params['school']]
          del proc_dict[params['school']]
          self.missingdbdict[params['school']] = result['missingdb']
          self.missingfilesdict[params['school']] = result['missingfiles']
          outlist['data'] = {
            'correct' : len(result['correct']),
            'missingdb' : len(result['missingdb']),
            'missingfiles' : len(result['missingfiles']),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingdb':	
        with lock_dict[params['school']]:
          proc_dict[params['school']] = Process(target=fixmissingdb, args=(params['school'],))
          pipe_dict[params['school']] = Pipe()
          proc_dict[params['school']].start()
          pipe_dict[params['school']][OUT].send(self.missingdbdict[params['school']])
          proc_dict[params['school']].join()
          del pipe_dict[params['school']]
          del proc_dict[params['school']]
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingfiles':	
        with lock_dict[params['school']]:
          proc_dict[params['school']] = Process(target=fixmissingfiles, args=(params['school'],))
          pipe_dict[params['school']] = Pipe()
          proc_dict[params['school']].start()
          pipe_dict[params['school']][OUT].send(self.missingfilesdict[params['school']])
          proc_dict[params['school']].join()
          del pipe_dict[params['school']]
          del proc_dict[params['school']]
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'checkrecfiles':
        with check_rec_lock:
          check_rec_proc = Process(target=checkrecordings, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          result = check_rec_pipe[IN].recv()
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
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
          await self.send(dumps(outlist))	

      elif params['command'] == 'fixtemp_rec':	
        with check_rec_lock:
          check_rec_proc = Process(target=fixtemp_rec, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          check_rec_pipe[OUT].send(self.fileset_c)
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingdb_rec':	
        with check_rec_lock:
          check_rec_proc = Process(target=fixmissingdb_rec, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          check_rec_pipe[OUT].send(self.rec_missingdb)
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingfiles_rec':	
        with check_rec_lock:
          check_rec_proc = Process(target=fixmissingfiles_rec, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          check_rec_pipe[OUT].send(self.rec_missingfiles)
          check_rec_pipe[OUT].send(self.dbtimedict)
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'checkevents':
        with check_rec_lock:
          check_rec_proc = Process(target=checkevents, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          result = check_rec_pipe[IN].recv()
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
          #self.missingevents = result['missingevents'] 
          self.missingframes = result['missingframes'] 
          outlist['data'] = {
            'correct' : result['correct'],
            'missingevents' : 0,
            'missingframes' : len(self.missingframes),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingevents':	
        #not implemented. This case is not possible because of database logic
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingframes':		
        with check_rec_lock:
          check_rec_proc = Process(target=fixmissingframes, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          check_rec_pipe[OUT].send(self.missingframes)
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'checkframes':
        with check_rec_lock:
          check_rec_proc = Process(target=checkframes, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          result = check_rec_pipe[IN].recv()
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
        self.missingdblines = result['missingdblines']
        self.missingfiles = result['missingfiles']
        outlist['data'] = {
          'correct' : result['correct'],
          'missingdblines' : len(self.missingdblines),
          'missingfiles' : len(self.missingfiles),
        }
        logger.debug('--> ' + str(outlist))
        await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingframesdb':	
        with check_rec_lock:
          check_rec_proc = Process(target=fixmissingframesdb, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          check_rec_pipe[OUT].send(self.missingdblines)
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

      elif params['command'] == 'fixmissingframesfiles':	
        with check_rec_lock:
          check_rec_proc = Process(target=fixmissingframesfiles, )
          check_rec_pipe = Pipe()
          check_rec_proc.start()
          check_rec_pipe[OUT].send(self.missingfiles)
          check_rec_proc.join()
          check_rec_pipe = None
          check_rec_proc = None
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(dumps(outlist))	

    else:
      await self.close()

#*****************************************************************************
# admintools
#*****************************************************************************

def scanoneip(ipstring, myports):
  portlist = []
  for port in myports:
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(0.2)
    try:
      result = s.connect_ex((ipstring, port))
    except gaierror:
      return(None)
    s.close()
    if result == 0:
      portlist.append(port)
  if portlist:
    result = {}
    result['ip'] = ipstring
    try:
      result['name'] = gethostbyaddr(ipstring)[0]
    except herror:
      result['name'] = 'name unknown'
    result['ports'] = portlist
    return(result)
  else:
    return(None)  

class admintools(AsyncWebsocketConsumer):

  async def connect(self):
    await self.accept()
    
  async def check_create_stream_priv(self):
    if self.scope['user'].is_superuser:
      return(True)
    else:
      limit = await getonelinedict(
        userinfo, 
        {'user' : self.scope['user'].id, }, 
        ['allowed_streams',]
      )
      limit = limit['allowed_streams']
      streamcount = await countfilter(
        dbstream, 
        {'creator' : self.scope['user'].id, 'active' : True,},
      )
      return(streamcount < limit)  
    
  async def check_create_school_priv(self):
    if self.scope['user'].is_superuser:
      return(True)
    else:
      limit = await getonelinedict(
        userinfo, 
        {'user' : self.scope['user'].id, }, 
        ['allowed_schools',]
      )
      limit = limit['allowed_schools']
      schoolcount = await countfilter(
        school, 
        {'creator' : self.scope['user'].id, 'active' : True,}
      )
      return(schoolcount < limit)  

  async def receive(self, text_data):
    logger.debug('<-- ' + text_data)
    params = loads(text_data)['data']	
    outlist = {'tracker' : loads(text_data)['tracker']}	

#*****************************************************************************
# functions for the client
#*****************************************************************************

    if params['command'] == 'scanoneip':
      if not await self.check_create_stream_priv():
        await self.close()
      if self.mycam.get_user(name=params['user']):
        self.mycam.set_users(name=params['user'], passwd=params['pass'])
      else:
        self.mycam.create_users(name=params['user'], passwd=params['pass'])
      cmds = ['ffprobe', '-v', 'fatal', '-print_format', 'json', 
        '-show_streams', params['camurl']]
      p = Popen(cmds, stdout=PIPE)
      output, _ = p.communicate()
      outlist['data'] = loads(output)
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'scanips':
      contactlist = []
      if self.scope['user'].is_superuser:
        if params['portaddr']:
          portlist = [params['portaddr'], ]
        else:
          portlist = [80, 443, 554, 1935, ]
        for item in my_net.hosts():        
          if item != my_ip:
            if (checkresult := scanoneip(str(item), portlist)):
              contactlist.append(checkresult)
      outlist['data'] = contactlist
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'scanonvif':
      contactlist = []
      if self.scope['user'].is_superuser:
        portlist = [params['portaddr'], ]
        if params['ip']:
          iplist = (params['ip'], )
        else:
          iplist = my_net.hosts()
        print(iplist)
        for item in iplist:        
          if item != my_ip:
            if (checkresult := scanoneip(str(item), portlist)):
              self.mycam = c_camera(
                onvif_ip=checkresult['ip'], 
                onvif_port=params['portaddr'], 
                admin_user=params['admin'], 
                admin_passwd=params['pass'],
              )
              if self.mycam.status == 'OK':
                for item in self.mycam.deviceinfo:
                  checkresult[item] = self.mycam.deviceinfo[item]
                if is_valid_IP_Address(params['ip']):
                  checkresult['urlscheme'] = self.mycam.urlscheme 
                else:
                  partitioned = self.mycam.urlscheme.partition('@')
                  print(partitioned)
                  leftpart = partitioned[0] + partitioned[1]
                  print(leftpart)
                  partitioned = partitioned[2].partition(':')
                  print(partitioned)
                  rightpart = partitioned[1] + partitioned[2]
                  checkresult ['urlscheme'] = (leftpart + params['ip'] + rightpart)
                contactlist.append(checkresult)
      outlist['data'] = contactlist
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'installcam':
      if not await self.check_create_stream_priv():
        await self.close()
      myschools = await filterlinesdict(school, {'active' : True, }, ['id', ])
      myschool = myschools[0]['id']
      newstream = dbstream()
      if 'name' in params:
        newstream.name = params['name']
      newstream.cam_url = params['camurl']
      newstream.cam_video_codec = params['videocodec']
      if params['audiocodec'] is None:
        newstream.cam_audio_codec = -1
      else:  
        newstream.cam_audio_codec = params['audiocodec']
      newstream.cam_xres = params['xresolution']
      newstream.cam_yres = params['yresolution']
      newstream.eve_school_id = myschool
      newstream.creator = self.scope['user']
      newlineid = await savedbline(newstream)
      if not self.scope['user'].is_superuser:
        myaccess = access_control()
        myaccess.vtype = 'X'
        myaccess.vid = newlineid
        myaccess.u_g_nr = self.scope['user'].id
        myaccess.r_w = 'W'
        await savedbline(myaccess)
      while redis.get_start_stream_busy():
        sleep(long_brake)
      redis.set_start_stream_busy(newstream.id)
      while (not (newstream.id in  streams)):
        sleep(long_brake)
      outlist['data'] = {'id' : newstream.id, }
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'makeschool':
      if not await self.check_create_school_priv():
        await self.close()
      if using_websocket or remote_trainer:
        from websocket import WebSocket
      newschool = school()
      newschool.name = params['name']
      newschool.creator = self.scope['user']
      await savedbline(newschool)
      if using_websocket or remote_trainer:
        if remote_trainer:
          trainer_type = 2
        else:
          trainer_type = 3  
        school_dict = await getonelinedict(school, 
          {'id': newschool.id, }, 
          ['tf_worker', 'e_school', 'trainer'])
        worker_dict = await getonelinedict(worker, 
          {'id': school_dict['tf_worker'], }, 
          ['wsserver', 'wspass', 'wsname', 'wsid', ])
        await updatefilter(trainer, 
          {'id': school_dict['trainer'], }, 
          {
            't_type' : trainer_type,
            'wsserver' : worker_dict['wsserver'], 
            'wsname' : worker_dict['wsname'], 
            'wspass' : worker_dict['wspass'], 
            'active' : True, 
          }, )
      else:
        school_dict = await getonelinedict(school, 
          {'id': newschool.id, }, 
          ['tf_worker', 'trainer'])
        await updatefilter(trainer, 
          {'id': school_dict['trainer'], }, 
          {
            't_type' : 1,
            'active' : True, 
          }, )
      schooldir = schoolsdir + 'model' + str(newschool.id) + '/'
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
        ws.connect(worker_dict['wsserver'] + 'ws/schoolutil/')
        outdict = {
          'code' : 'makeschool',
          'name' : 'CL' + str(worker_dict['wsid'])+': ' + params['name'],
          'pass' : worker_dict['wspass'],
          'user' : worker_dict['wsid'],
        }
        ws.send(json.dumps(outdict), opcode=1) #1 = Text
        resultdict = json.loads(ws.recv())
        ws.close()
      if not using_websocket:
        print(schoolsdir, schooldir)
        print('copy', schoolsdir + 'model1/model/' + model_type + '.h5', 
          schooldir + 'model/' + model_type + '.h5')
        copyfile(schoolsdir + 'model1/model/' + model_type + '.h5', 
          schooldir + 'model/' + model_type + '.h5')
      if using_websocket or remote_trainer:
        if resultdict['status'] == 'OK':
          await updatefilter(school, 
            {'id' : newschool.id, }, 
            {'dir' : schooldir, 'e_school' : resultdict['school'], })
          await updatefilter(trainer, 
            {'id' : school_dict['trainer'], }, 
            {'wsserver' : worker_dict['wsserver'], 
            'wsname' : worker_dict['wsname'], 
            'wspass' : worker_dict['wspass'], 
            'active' : True, 
            't_type' : trainer_type,
            })
      else:
        resultdict = {'status' : 'OK', }
        await updatefilter(school, 
          {'id' : newschool.id, }, 
          {'dir' : schooldir, 'model_type' : model_type, })
      if resultdict['status'] == 'OK':
        if not self.scope['user'].is_superuser:
          myaccess = access_control()
          myaccess.vtype = 'S'
          myaccess.vid = newschool.id
          myaccess.u_g_nr = self.scope['user'].id
          myaccess.r_w = 'W'
          await savedbline(myaccess)
      else:
        await updatefilter(school, 
          {'id' : newschool.id, }, 
          {'active' : False, })
      outlist['data'] = resultdict
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'linkworker':
      if not self.scope['user'].is_superuser:
        await self.close()
      from websocket import WebSocket
      ws = WebSocket()
      ws.connect(params['server'] + 'ws/admintools/')
      outdict = {
        'command' : 'linkserver',
        'user' : params['user'],
        'pass' : params['pass'],
      }
      print(outdict)
      ws.send(json.dumps({
        'tracker' : 0, 
        'data' : outdict, 
      }), opcode=1) #1 = Text
      resultdict = json.loads(ws.recv())
      print(resultdict)
      ws.close()
      if resultdict['data']['status'] == 'new': 
        await updatefilter(worker, {'id' : params['workernr'], }, {
          'active' : True,
          'gpu_sim' : -1,
          'use_websocket' : using_websocket,
          'wsserver' : params['server'],
          'wsname' : resultdict['data']['user'],
          'wspass' : params['pass'],
          'wsid' : resultdict['data']['idx'],
        })
        while redis.get_start_worker_busy():
          sleep(long_brake)
        redis.set_start_worker_busy(params['workernr'])
        schooldict = await filterlinesdict(school, 
          {'tf_worker' : params['workernr'], }, 
          ['id', ],
        )
        streamlist = []
        for item1 in schooldict:
          streamdict = await filterlinesdict(dbstream,
            {'eve_school' : item1['id'], },
            ['id', ],
          )
          for item2 in streamdict:
            streamlist.append(item2['id'])
        for i in streamlist:
          while redis.get_start_stream_busy(): 
            sleep(long_brake)
          redis.set_start_stream_busy(i)
      outlist['data'] = resultdict['data']['status'] 
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	
      
    elif params['command'] == 'checkserver':
      outlist['data'] = {} 
      if not self.scope['user'].is_superuser:
        await self.close() 
      from websocket import WebSocket
      from websocket._exceptions import WebSocketAddressException
      ws = WebSocket()
      try:
        ws.connect(params['server'] + 'ws/admintools/')
        outdict = {
          'command' : 'getinfo',
        }
        print(outdict)
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
      await self.send(dumps(outlist))	

#*****************************************************************************
# functions for the server
#*****************************************************************************

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
      await self.send(dumps(outlist))	
      
    elif params['command'] == 'getinfo':
      filename = textpath+'serverinfo.html'
      try:
        with open(filename, 'r', encoding='UTF-8') as f:
          result = f.read()
      except FileNotFoundError:
        result = 'No Info: ' + textpath + 'serverinfo.html does not exist...'
      outlist['data'] = result
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

