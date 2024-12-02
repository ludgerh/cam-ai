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
from shutil import rmtree
from time import sleep
from setproctitle import setproctitle
from multiprocessing import Process
from logging import getLogger
from traceback import format_exc
from zipfile import ZipFile, ZIP_DEFLATED
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from channels.generic.websocket import AsyncWebsocketConsumer
from camai.c_settings import safe_import
from tools.c_logger import log_ini
from tools.l_tools import djconf, displaybytes
from tools.l_smtp import smtp_send_mail
from tools.c_redis import myredis
from tf_workers.models import school, worker
from trainers.models import trainer
from streams.models import stream as dbstream
from users.models import userinfo
from access.models import access_control
from access.c_access import access
from users.models import userinfo
from users.userinfo import afree_quota
from .health import totaldiscspace, freediscspace

db_password = safe_import('db_password') 
hw_type = safe_import('hw_type') 
os_version = safe_import('os_version') 
mydomain = safe_import('mydomain') 

OUT = 0
IN = 1

if mydomain:
  myserver = mydomain
else:
  myserver = 'localhost'  

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

#*****************************************************************************
# health
#*****************************************************************************

class health(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (health)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def receive(self, text_data):
    try:
      logger.debug('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

      if params['command'] == 'getdiscinfo':
        if self.scope['user'].is_superuser:
          avaible = freediscspace
          total = totaldiscspace
        else:  
          infoline = await userinfo.objects.aget(user = self.scope['user'])
          avaible = max(0, infoline.storage_quota - infoline.storage_used)
          total = infoline.storage_quota
        outlist['data'] = {
          'total' : total,
          'free' : avaible,
          'totalstr' : displaybytes(total),
          'freestr' : displaybytes(avaible),
        }
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

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
      or (str(item.relative_to(dirpath)).startswith(
        str(recordingspath.relative_to(Path(datapath)))+'/C'
      ))
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
    
  async def check_create_school_priv(self, user):
    # todo: Add volume quota
    if user.is_superuser:
      return((0,1))
    else:
      userinfoline = await userinfo.objects.aget(user=user)
      limit = userinfoline.allowed_schools
      schoolcount = await school.objects.filter(creator=user, active=True).acount()
      return((schoolcount, limit))

  async def receive(self, text_data):
    try:
      #logger.info('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

#*****************************************************************************
# functions for the client
#*****************************************************************************

      if params['command'] == 'makeschool': #The clients part
        userline = self.scope['user'] # More to come
        if userline.is_anonymous:
          userline = await User.objects.aget(id = params['user'])
          hash = userline.password
          if not check_password(params['pass'], hash):
            outlist['data'] = {'status' : 'noauth', 'domain' : myserver}
            await self.send(json.dumps(outlist))
            return()
        quota =  await self.check_create_school_priv(userline)
        if quota[0] >= quota[1]:
          outlist['data'] = {'status' : 'nomoreschools', 'quota' : quota, 'domain' : myserver}
          await self.send(json.dumps(outlist))
          return()
        trainerline = await trainer.objects.aget(id=params['trainer_nr']) 
        schoolline = school()
        schoolline.name = params['name']
        schoolline.creator = userline
        schoolline.trainer = trainerline
        await schoolline.asave() 
        schoolline.dir = schoolsdir + 'model' + str(schoolline.id) + '/'
        await schoolline.asave(update_fields=('dir', ))
        await aiofiles.os.makedirs(schoolline.dir+'frames', exist_ok=True)
        await aiofiles.os.makedirs(schoolline.dir+'model', exist_ok=True)
        if trainerline.t_type in {2, 3}:
          from aiohttp import ClientSession
          async with ClientSession() as session:
            async with session.ws_connect(trainerline.wsserver + 'ws/aadmintools/') as ws:
              outdict = json.loads(text_data)
              outdict['data']['name'] = 'CL' + str(trainerline.wsid)+': ' + params['name']
              outdict['data']['pass'] = trainerline.wspass
              outdict['data']['user'] = trainerline.wsid
              outdict['data']['trainer_nr'] = 1
              await ws.send_str(json.dumps(outdict))
              message = await ws.receive()
              resultdict = json.loads(message.data)['data']
        else:
          resultdict = {'status' : 'OK', 'school' : schoolline.id}      
        if trainerline.t_type in {1, 2} and resultdict['status'] == 'OK':
          if await afree_quota(userline):
            for ext in ('.keras', '.tflite'):
              filename = model_type + ext
              if await aiofiles.os.path.exists(schoolsdir + 'model1/model/' + filename):
                await aioshutil.copy(schoolsdir + 'model1/model/' + filename,
                  schoolline.dir + 'model/' + filename)
          else:
            resultdict = {'status' : 'nomorequota', 'domain' : myserver}
        if trainerline.t_type in {2, 3}:
          if resultdict['status'] == 'OK':
            schoolline.e_school = resultdict['school']
            resultdict['school'] = schoolline.id
            await schoolline.asave(update_fields=('e_school', ))
        else:
          if resultdict['status'] == 'OK':
            resultdict['quota'] = (quota[0] + 1, quota[1])
            schoolline.model_type = model_type
            await schoolline.asave(update_fields=('model_type', ))
        if resultdict['status'] == 'OK':
          if not self.scope['user'].is_superuser:
            myaccess = access_control()
            myaccess.vtype = 'S'
            myaccess.vid = schoolline.id
            myaccess.u_g_nr = userline.id
            myaccess.r_w = 'W'
            await myaccess.asave()
            await access.read_list_async()
        else:
          if await aiofiles.os.path.exists(schoolline.dir):
            await aioshutil.rmtree(schoolline.dir)
          schoolline.adelete()
        outlist['data'] = resultdict
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

      elif params['command'] == 'linkserver-c':
        if not self.scope['user'].is_superuser:
          await self.close()
        if params['user']:  
          from aiohttp import ClientSession
          async with ClientSession() as session:
            async with session.ws_connect(params['server'] + 'ws/aadmintools/') as ws:
              outdict = {
                'command' : 'linkserver-s',
                'user' : params['user'],
                'pass' : params['pass'],
              }
              await ws.send_str(json.dumps({
                'tracker' : 0, 
                'data' : outdict, 
              }))
              message = await ws.receive()
              resultdict = json.loads(message.data)
          if params['type'] == 'w': #Worker 
            if resultdict['data']['status'] == 'new': 
              myworker = await worker.objects.aget(id=params['item_nr'])
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
              redis.set_start_worker_busy(params['item_nr'])
              myschools = school.objects.filter(tf_worker=params['item_nr'])
              streamlist = []
              async for item1 in myschools:
                mystreams = dbstream.objects.filter(eve_school=item1, active=True, )
                async for item2 in mystreams:
                  streamlist.append(item2.id)
              for i in streamlist:
                while redis.get_start_stream_busy(): 
                  sleep(long_brake)
                redis.set_start_stream_busy(i)
          elif params['type'] == 't': #Trainer
            if resultdict['data']['status'] == 'new': 
              mytrainer = await trainer.objects.aget(id=params['item_nr'])
              mytrainer.wsserver=params['server']
              mytrainer.wsname=resultdict['data']['user']
              mytrainer.wspass=params['pass']
              mytrainer.wsid=resultdict['data']['idx']
              await mytrainer.asave(update_fields=(
                'wsserver',
                'wsname',
                'wspass',
                'wsid',
              ))
              while redis.get_start_trainer_busy():
                sleep(long_brake)
              redis.set_start_trainer_busy(mytrainer.id)
          outlist['data'] = resultdict['data']['status'] 
        else:
          if params['type'] == 'w': #Worker 
            myworker = await worker.objects.aget(id=params['item_nr'])
            myworker.wsname=''
            await myworker.asave(update_fields=('wsname',))
          elif params['type'] == 't': #Trainer
            mytrainer = await trainer.objects.aget(id=params['item_nr'])
            mytrainer.wsname=''
            await mytrainer.asave(update_fields=('wsname',))
          outlist['data'] = 'unlinked' 
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

      elif params['command'] == 'linkserver-s':
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
        #logger.info('--> ' + str(outlist))
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
        
      elif params['command'] == 'shutdown':
        if not self.scope['user'].is_superuser:
          await self.close()
        redis.set_shutdown_command(1)
        while redis.get_watch_status():
          await asleep(long_brake) 
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
      elif params['command'] == 'upgrade':
        if not self.scope['user'].is_superuser:
          await self.close()
        basepath = getcwd() 
        chdir('..')
        print('#####', params['url'])
        async with aiohttp.ClientSession() as session:
          async with session.get(params['url']) as result:
            response = await result.content.read()
        with ZipFile(io.BytesIO(response)) as z:
          z.extractall("temp/expanded")
        if params['special']:
          zipresult = glob('temp/expanded/cam-ai-*')[0]
        else:
          zipresult = glob('temp/expanded/ludgerh-cam-ai-*')[0]
        if await aiofiles.os.path.exists('temp/backup'):
          await aioshutil.rmtree('temp/backup')
        await aioshutil.move(basepath, 'temp/backup') 
        await aioshutil.move(zipresult, basepath) 
        await aioshutil.copy(
          basepath + '/requirements.raspi_12',
          basepath + '/requirements.raspi12'
        )
        await aioshutil.copy(
          'temp/backup/camai/passwords.py', 
          basepath + '/camai/passwords.py'
        )
        if await aiofiles.os.path.exists(
          'temp/backup/accounts/templates/django_registration/privacy.html'
        ):
          await aioshutil.copy(
            'temp/backup/accounts/templates/django_registration/privacy.html', 
            basepath + '/accounts/templates/django_registration/privacy.html'
          )
        if await aiofiles.os.path.exists(
          'temp/backup/accounts/templates/django_registration/terms.html'
        ):
          await aioshutil.copy(
            'temp/backup/accounts/templates/django_registration/terms.html', 
            basepath + '/accounts/templates/django_registration/terms.html'
          )
        await aioshutil.move('temp/backup/' + datapath, basepath + '/' + datapath)
        if await aiofiles.os.path.exists('temp/backup/plugins/'):
          await aioshutil.move('temp/backup/plugins/', basepath + '/plugins/')
        chdir(basepath)
        if hw_type == 'raspi':
          cmd = 'source ~/miniforge3/etc/profile.d/conda.sh; '
        if hw_type == 'pc':
          cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
        cmd += 'conda activate tf; '
        cmd += 'pip install --upgrade pip; '
        cmd += 'pip install -r requirements.' + hw_type + '_' + os_version + '; '
        cmd += 'python manage.py migrate; '
        #result = subprocess.check_output(cmd, shell=True, executable='/bin/bash').decode()
        p = await asyncio.create_subprocess_shell(
          cmd, 
          stdout=asyncio.subprocess.PIPE, 
          executable='/bin/bash',
        )
        output, _ = await p.communicate()
        for line in output.decode().split('\n'):
          logger.info(line);
        redis.set_shutdown_command(2)
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        while redis.get_watch_status():
          await asleep(long_brake) 
        
      elif params['command'] == 'sendlogs':
        if not self.scope['user'].is_superuser:
          await self.close()
        datapath = djconf.getconfig('datapath', 'data/')
        logpath = djconf.getconfig('logdir', default = datapath + 'logs/')
        smtp_send_mail(
          'The Log files',
          'These are the Log Files',
          'CAM-AI Emailer<' + settings.EMAIL_FROM + '>',
          ['support@booker-hellerhoff.de', ],
          html_message = 'These are the Log Files (HTML)',
          logger = logger,
          attachments = (
            ('c_server.err', logpath + 'c_server.err', 'text/plain'), 
            ('c_server.log', logpath + 'c_server.log', 'text/plain'), 
          ),
        )  
          
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
    except:
      logger.error('Error in consumer: ' + logname + ' (admin_tools_async)')
      logger.error(format_exc())
      logger.handlers.clear()

