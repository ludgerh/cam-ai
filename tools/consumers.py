"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
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
import os
from contextlib import suppress
from asgiref.sync import sync_to_async
from pathlib import Path
from glob import glob
from shutil import rmtree
from time import sleep
from setproctitle import setproctitle
from multiprocessing import Process
from logging import getLogger
from traceback import format_exc
from zipfile import ZipFile, ZIP_DEFLATED

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'camai.settings')
django.setup()

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import check_password
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.l_tools import djconf, displaybytes
from tools.l_smtp import l_smtp, l_msg
from tools.l_break import a_break_type, BR_LONG
from camai.c_settings import safe_import
from camai.version import version
from tools.c_logger import log_ini
from startup.redis import my_redis as startup_redis
from tools.c_tools import aget_smtp_conf
from tf_workers.models import school, worker
from trainers.models import trainer, trainframe_imex
from streams.models import stream as dbstream
from users.models import userinfo
from access.models import access_control
from access.c_access import access
from users.userinfo import afree_quota
from tf_workers.redis import my_redis as tf_workers_redis
from .redis import my_redis as tools_redis
from .health import my_health_runner

DB_DATABASE = safe_import('db_database') 
DB_PASSWORD = safe_import('db_password') 
HW_TYPE = safe_import('hw_type') 
OS_VERSION = safe_import('os_version') 
MYDOMAIN = safe_import('mydomain') 

OUT = 0
IN = 1

if MYDOMAIN:
  myserver = MYDOMAIN
else:
  myserver = 'localhost'  

USING_WEBSOCKET = worker.objects.get(id = 1).use_websocket
if school.objects.count():
  MODEL_TYPE = school.objects.first().model_type
else:
  MODEL_TYPE = 'NotDefined'

LOGNAME = 'ws_tools'
logger = getLogger(LOGNAME)
log_ini(logger, LOGNAME)
BASE_PATH = Path(settings.BASE_DIR)
DATAPATH = djconf.getconfigpath('datapath', default = 'data/', base = BASE_PATH)
LOGPATH = djconf.getconfigpath('logdir', default = 'logs/', base = DATAPATH)
RECORDINGSPATH = djconf.getconfigpath(
  'recordingspath', 
  default = 'recordings/', 
  base = DATAPATH,
)
TEXTPATH = djconf.getconfigpath('textpath', default = 'texts/', base = DATAPATH)
smtp_email = djconf.getconfig('smtp_email', forcedb=False)
TEXTPATH.mkdir(parents=True, exist_ok=True)
SCHOOLSPATH = djconf.getconfigpath('schools_dir', default = 'schools/', base = DATAPATH)
PARENTPATH = BASE_PATH.parent
(PARENTPATH / 'temp').mkdir(parents=True, exist_ok=True)

#*****************************************************************************
# health
#*****************************************************************************

class health(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      await self.accept()
    except:
      logger.error('Error in consumer: ' + LOGNAME + ' (health)')
      logger.error(format_exc())

  async def receive(self, text_data):
    try:
      #logger.info('<-- ' + text_data)
      data = json.loads(text_data)
      params = data.get('data', {})
      outlist = {'tracker': data.get('tracker')}


      if params['command'] == 'getdiscinfo':
        if self.scope['user'].is_superuser:
          avaible = my_health_runner.freediscspace
          total = my_health_runner.totaldiscspace
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
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

      if params['command'] == 'get_tf_info':
        if self.scope['user'].is_superuser:
          outlist['data'] = {
            'buf_size' : tf_workers_redis.get_buf_size(1),
            'buf_size_10' : round(tf_workers_redis.get_buf_size_10(1), 4),
            'block_size' : tf_workers_redis.get_block_size(1),
            'block_size_10' : round(tf_workers_redis.get_block_size_10(1), 4),
            'proc_time' : round(tf_workers_redis.get_proc_time(1), 4),
            'proc_time_10' : round(tf_workers_redis.get_proc_time_10(1), 4),
          }
        else:  
          outlist['data'] = {
            'buf_size' : 0.0,
            'buf_size_10' : 0.0,
            'block_size' : 0.0,
            'block_size_10' : 0.0,
            'proc_time' : 0.0,
            'proc_time_10' : 0.0,
          }
        if outlist['data']['block_size']:
          outlist['data']['one_image'] = round(
            outlist['data']['proc_time'] / outlist['data']['block_size'], 
            4, 
          )
        else:
          outlist['data']['one_image'] = 0.0 
        if outlist['data']['block_size_10']:
          outlist['data']['one_image_10'] = round(
            outlist['data']['proc_time_10'] / outlist['data']['block_size_10'], 
            4,
          )
        else:
          outlist['data']['one_image_10'] = 0.0 
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

    except:
      logger.error('Error in consumer: ' + LOGNAME + ' (health)')
      logger.error(format_exc())


#*****************************************************************************
# tools_async
#*****************************************************************************
        
def compress_backup(idx, school_nr):
  setproctitle('CAM-AI-Backup-Compression')
  os.nice(19)
  save_path = PARENTPATH /'temp' / 'backup'
  save_path.mkdir(parents=True, exist_ok=True)
  if school_nr:
    zip_path = save_path / f'CAM-AI-school-{school_nr}.zip'
  else:
    zip_path = save_path / f'CAM-AI-backup-{version}.zip'
  zip_path.unlink(missing_ok=True) 
  tools_redis.set_zip_info(idx, 'Compressing Database...')
  env = dict(os.environ, MYSQL_PWD = DB_PASSWORD)
  if school_nr:
    sel = 'select '
    sel += ",".join(trainframe_imex)
    sel += f' from trainers_trainframe where deleted=0 and school={school_nr};' 
    cmd = [
      'mariadb',
      '--user=CAM-AI',
      '--host=localhost',
      '-N',
      '-e',
      sel,
      DB_DATABASE,
    ]
    sql_path = save_path / 'db.dat'
  else:
    cmd = [
      'mariadb-dump',
      '--user=CAM-AI',
      '--host=localhost',
      '--single-transaction',
      '--quick',
      '--skip-lock-tables',
      DB_DATABASE,
    ]
    sql_path = save_path / 'db.sql'
  with sql_path.open("wb") as f:
    subprocess.run(cmd, check=True, env=env, stdout=f)
  with ZipFile(zip_path, "w", ZIP_DEFLATED) as zip_file:
    zip_file.write(sql_path, sql_path.name)
  conf_path = save_path / 'upload.cfg'  
  if school_nr:
    school_line = school.objects.get(id = school_nr)
    conf_path.write_text(
      f'version = {version}\n' 
        + f'schoolname = {school_line.name}\n'
        + f'delegation_level = {school_line.delegation_level}\n', 
      encoding='utf-8'
    )
  else:
    school_name = 'none'  
    conf_path.write_text(
      f'version = {version}\n' 
        + f'schoolname = none\n', 
      encoding='utf-8'
    )
  with ZipFile(zip_path, "a", ZIP_DEFLATED) as zip_file:
    zip_file.write(conf_path, conf_path.name)
  sql_path.unlink(missing_ok=True) 
  conf_path.unlink(missing_ok=True) 
  if school_nr:
    path_to_upload = SCHOOLSPATH / f'model{school_nr}'
  else:
    path_to_upload = DATAPATH
  glob_list = []
  if school_nr:
    for item in path_to_upload.rglob('*'):
      glob_list.append(item)
  else:
    for item in path_to_upload.rglob('*'):
      if item == RECORDINGSPATH:
        continue
      rel = item.relative_to(path_to_upload)
      if rel.parts and rel.parts[0] == "static":
        continue
      if item.is_relative_to(RECORDINGSPATH) and item.name.startswith('C'):
        continue
      glob_list.append(item)
  total =  len(glob_list)
  count = 0
  transmitted = 0
  with ZipFile(zip_path, "a", ZIP_DEFLATED) as zip_file:
    for item in glob_list:
      count += 1
      zip_file.write(item, item.relative_to(path_to_upload))
      percentage = (count / total * 100)
      if percentage >= transmitted + 0.1:
        tools_redis.set_zip_info(idx, str(round(percentage, 1)) + '% compressed')
        transmitted = percentage
  
class admin_tools_async(AsyncWebsocketConsumer):

  backup_proc_dict = {}

  async def connect(self):
    try:
      await self.accept()
    except:
      logger.error('Error in consumer: ' + LOGNAME + ' (admin_tools_async)')
      logger.error(format_exc())
    
  async def check_create_school_priv(self, user):
    # todo: Add volume quota
    if user.is_superuser:
      return((0,1))
    else:
      userinfoline = await userinfo.objects.aget(user=user)
      limit = userinfoline.allowed_schools
      schoolcount = await school.objects.filter(creator=user, active=True).acount()
      return((schoolcount, limit))

  async def receive(self, text_data =None):
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
          outlist['data'] = {
            'status' : 'nomoreschools', 
            'quota' : quota, 
            'domain' : myserver,
          }
          await self.send(json.dumps(outlist))
          return()
        schoolline = school()
        schoolline.name = params['name']
        schoolline.creator = userline
        await schoolline.asave() 
        t_query = trainer.objects.filter(active = True)
        trainerline = await t_query.afirst()
        schoolline.dir = str(SCHOOLSPATH / f'model{schoolline.id}') + os.sep
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
              outdict['data']['delegation_level'] += 1
              await ws.send_str(json.dumps(outdict))
              message = await ws.receive()
              resultdict = json.loads(message.data)['data']
        else:
          resultdict = {'status' : 'OK', 'school' : schoolline.id} 
        if trainerline.t_type in {1, 2, 3} and resultdict['status'] == 'OK':
          if await afree_quota(userline):
            for ext in ('.keras', '.tflite'):
              filename = f'{MODEL_TYPE}{ext}'
              with suppress(FileNotFoundError):
                await aioshutil.copy(
                  SCHOOLSPATH / 'model1' / 'model' / filename,
                  Path(schoolline.dir) / 'model' / filename,
                )
          else:
            resultdict = {'status' : 'nomorequota', 'domain' : myserver}
        if resultdict['status'] == 'OK':
          schoolline.delegation_level = params['delegation_level']
          await schoolline.asave(update_fields = ('delegation_level', ))
          if trainerline.t_type in {2, 3}:
            schoolline.e_school = resultdict['school']
            resultdict['school'] = schoolline.id
            await schoolline.asave(update_fields = ('e_school', ))
          else:
            resultdict['quota'] = (quota[0] + 1, quota[1])
            schoolline.model_type = MODEL_TYPE
            await schoolline.asave(update_fields = ('model_type', ))
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
          await schoolline.adelete()
        outlist['data'] = resultdict
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

      elif params['command'] == 'linkserver-c':
        if not self.scope['user'].is_superuser:
          await self.close()
          return()
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
              myworker.use_websocket = USING_WEBSOCKET
              myworker.wsserver = params['server']
              myworker.wsname = resultdict['data']['user']
              myworker.wspass = params['pass']
              myworker.wsid = resultdict['data']['idx']
              await myworker.asave(update_fields = (
                'gpu_sim',
                'use_websocket',
                'wsserver',
                'wsname',
                'wspass',
                'wsid',
              ))
              while startup_redis.get_start_worker_busy():
                await a_break_type(BR_LONG)
              startup_redis.set_start_worker_busy(params['item_nr'])
              myschools = school.objects.filter(tf_worker=params['item_nr'])
              streamlist = []
              async for item1 in myschools:
                mystreams = dbstream.objects.filter(eve_school=item1, active=True, )
                async for item2 in mystreams:
                  streamlist.append(item2.id)
              for i in streamlist:
                while startup_redis.get_start_stream_busy(): 
                  await a_break_type(BR_LONG)
                startup_redis.set_start_stream_busy(i)
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
              while startup_redis.get_start_trainer_busy():
                await a_break_type(BR_LONG)
              startup_redis.set_start_trainer_busy(mytrainer.id)
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
          return()
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
        if 'school_nr' not in params:
          params['school_nr'] = None
        if not self.scope['user'].is_superuser:
          await self.close()
          return()
        idx = 0
        while idx in self.backup_proc_dict:
          idx += 1 
        tools_redis.purge_zip_info(idx) 
        self.backup_proc_dict[idx] = Process(
          target=compress_backup, 
          args=[idx, params['school_nr']],
        )
        self.backup_proc_dict[idx].start()
        while self.backup_proc_dict[idx].is_alive():
          if (my_info := tools_redis.get_zip_info(idx)):
            outlist['data'] = my_info.decode("utf-8")
            outlist['callback'] = True
            await self.send(json.dumps(outlist))	
          else:  
            await a_break_type(BR_LONG)
        outlist['data'] = 'OK'
        del outlist['callback']
        del self.backup_proc_dict[idx]
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

      elif params['command'] == 'linkserver-s':
        outlist['data'] = {}
        try:
          myuser = await User.objects.aget(username = params['user'])
        except User.DoesNotExist:
          myuser = None
        if myuser:
          if await sync_to_async(myuser.check_password)(params['pass']):
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
        filename = TEXTPATH / 'serverinfo.html'
        try:
          async with aiofiles.open(filename, mode='r', encoding='UTF-8') as f:
            result = await f.read()
        except FileNotFoundError:
          result = 'No Info: serverinfo.html does not exist...'
        outlist['data'] = result
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
      elif params['command'] == 'shutdown':
        if not self.scope['user'].is_superuser:
          await self.close()
          return()
        startup_redis.set_shutdown_command(10)
        #while startup_redis.get_shutdown_command() != 11:
        #  await a_break_type(BR_LONG)
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
      elif params['command'] == 'upgrade':
        if not self.scope['user'].is_superuser:
          await self.close()
          return()
        expand_path = PARENTPATH / 'temp' / 'expanded'  
        backup_path = PARENTPATH / 'temp' / 'backup'  
        async with aiohttp.ClientSession() as session:
          async with session.get(params['url']) as result:
            response = await result.content.read()
        with ZipFile(io.BytesIO(response)) as z:
          z.extractall(expand_path)
        if params['special']:
          zipresult = next(expand_path.glob('cam-ai-*'), None)
        else:
          zipresult = next(expand_path.glob('ludgerh-cam-ai-*'), None)
        with suppress(FileNotFoundError):
          await aioshutil.rmtree(backup_path)
        await aioshutil.move(BASE_PATH, backup_path) 
        await aioshutil.move(zipresult, BASE_PATH) 
        await aioshutil.copy(
          backup_path / 'camai' / 'passwords.py', 
          BASE_PATH / 'camai' / 'passwords.py',
        )
        with suppress(FileNotFoundError):
          await aioshutil.copy(
            backup_path / 'accounts' / 'templates' / 'registration' / 'privacy.html',
            BASE_PATH / 'accounts' / 'templates' / 'registration' / 'privacy.html',
          )
        with suppress(FileNotFoundError):
          await aioshutil.copy(
            backup_path / 'accounts' / 'templates' / 'registration' / 'terms.html',
            BASE_PATH / 'accounts' / 'templates' / 'registration' / 'terms.html',
          )
        with suppress(FileNotFoundError):
          await aioshutil.move(
            backup_path / 'plugins',
            BASE_PATH / 'plugins',
          )
        datapath_rel = DATAPATH.relative_to(BASE_PATH) #not complete if DATAPATH absolute
        await aioshutil.move(backup_path / datapath_rel, DATAPATH)
        
        if HW_TYPE == 'raspi':
          cmd = 'source ~/miniforge3/etc/profile.d/conda.sh; '
        if HW_TYPE == 'pc':
          cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
        cmd += 'conda activate tf; '
        cmd += 'pip install --upgrade pip; '
        cmd += 'pip install -r requirements.' + HW_TYPE + '_' + OS_VERSION + '; '
        cmd += 'python manage.py migrate; '
        p = await asyncio.create_subprocess_shell(
          cmd, 
          stdout=asyncio.subprocess.PIPE, 
          executable='/bin/bash',
        )
        output, _ = await p.communicate()
        for line in output.decode().split('\n'):
          logger.info(line);
        startup_redis.set_shutdown_command(20)
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        while True:
          await a_break_type(BR_LONG)
          
      elif params['command'] == 'sendlogs':
        smtp_conf = await aget_smtp_conf(extended_from = False)
        smtp_conf['sender_email'] = (
          'Logfile-Sender' + '<' + smtp_conf['sender_email'] + '>')
        my_smtp = l_smtp(**smtp_conf)
        await my_smtp.async_init()
        my_msg = l_msg(
          smtp_conf['sender_email'],
          'support@cam-ai.de',
          'The Log files from ' + smtp_conf['sender_email'],
          params['message'],
          html = params['message'].replace('\n', '<br>'),
        )
        my_msg.attach_file(LOGPATH + 'c_server.err') 
        my_msg.attach_file(LOGPATH + 'c_server.log')  
        await my_smtp.sendmail(
          smtp_conf['sender_email'],
          'support@cam-ai.de',
          my_msg,
        )
        if my_smtp.result_code:
          logger.error('SMTP: ' + my_smtp.answer)
          logger.error(str(my_smtp.last_error))
        await my_smtp.quit()
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))
    except:
      logger.error('Error in consumer: ' + LOGNAME + ' (admin_tools_async)')
      logger.error(format_exc())
