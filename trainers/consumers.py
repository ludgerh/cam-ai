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
import cv2 as cv
import numpy as np
import asyncio
import aiofiles
import aiofiles.os
import io
from asgiref.sync import sync_to_async
from os import path, makedirs
from math import inf
from time import time, sleep
from datetime import datetime
from multiprocessing import Process
from logging import getLogger
from random import randrange
from traceback import format_exc
from zipfile import ZipFile
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.forms.models import model_to_dict
from django.db import transaction, close_old_connections
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from camai.version import version
from tools.l_tools import djconf, seq_to_int, version_newer_or_equal
from tools.c_logger import log_ini
from access.c_access import access
from tools.tokens import maketoken_async
from tf_workers.models import school
from users.userinfo import afree_quota
from globals.c_globals import trainers
from .models import trainframe, fit, epoch, trainer as dbtrainer, img_size, model_type
from .train_worker_remote import train_once_remote

from random import randint

logname = 'ws_trainers'
logger = getLogger(logname)
log_ini(logger, logname)
default_modeltype = djconf.getconfig('default_modeltype', 'efficientnetv2-b0')
medium_brake = djconf.getconfigfloat('medium_brake', 0.1)
counter_dict = {}

async def get_trainer_nr(school_line):
  trainerlist = []
  async for item in dbtrainer.objects.filter(active = True):
    trainerlist.append(item)  
  if len(trainerlist) == 1:    
    result = trainerlist[0].id
  else:  
    result = -1
    length = inf
    shortest = []
    for item in trainerlist:   
      joblist = trainers[item.id].getqueueinfo() 
      if school_line.id in joblist:
        return((item.id, len(trainerlist)))
      elif len(joblist) < length:
        length = len(joblist)
        shortest = [item.id, ]
      elif len(joblist) == length:
        shortest.append(item.id)
    result = shortest.pop(randrange(len(shortest)))   
  return((result, len(trainerlist)))

#*****************************************************************************
# RemoteTrainer
#*****************************************************************************

@database_sync_to_async
def is_size_in_item(item, sizeline):
  return sizeline in item.img_sizes.all()

class remotetrainer(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      self.ws_session = None
      self.frameinfo = {}
      self.made_dirs = set()
      self.sizeline = None
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (remotetrainer)')
      logger.error(format_exc())

  async def disconnect(self, code):
    try:
      logger.debug('Disconnected, Code:'+ str(code)) 
      close_old_connections() 
    except:
      logger.error('Error in consumer: ' + logname + ' (remotetrainer)')
      logger.error(format_exc())      

  async def receive(self, text_data =None, bytes_data=None):
    global counter_dict
    try:
      if bytes_data: 
        #logger.info('<-- binary')
        if self.sizeline is None:
          self.cod_x = self.myschoolline.model_xin
          self.cod_y = self.myschoolline.model_yin
          self.sizeline, _ = await sync_to_async(img_size.objects.get_or_create)(
            x=self.cod_x, 
            y=self.cod_y, 
          )
        ram_file = io.BytesIO(bytes_data)
        if self.mytrainerline.t_type == 2:
          zip_buffer = io.BytesIO()  
          zip_content = ram_file.read()
          await self.ws.send_bytes(zip_content)
          await self.ws.receive()
        else:
          with ZipFile(ram_file) as myzip:
            i = len(myzip.namelist())
            for item in myzip.namelist():
              #logger.info('(' +str(i)+ ') Unpacking: ' + item)
              i -= 1
              if item.endswith(".bmp"):
                codpath = (self.myschoolline.dir
                  + 'coded/' + str(self.cod_x) + 'x' + str(self.cod_y) 
                  + '/' + item[:-4] + '.cod')
                mydir = path.dirname(codpath) 
                if mydir not in self.made_dirs:
                  await aiofiles.os.makedirs(mydir, exist_ok=True)
                  self.made_dirs.add(mydir)
                jpgdata = await asyncio.to_thread(myzip.read, item)
                img = await asyncio.to_thread(
                  cv.imdecode, 
                  np.frombuffer(jpgdata, np.uint8), 
                  cv.IMREAD_COLOR, 
                )
                if img.shape[1] != self.cod_x or  img.shape[0] != self.cod_y:
                  img = await asyncio.to_thread(cv.resize, img, (self.cod_x, self.cod_y))
                  jpgdata = await asyncio.to_thread(cv.imencode, ".jpg", img)
                  jpgdata = jpgdata[1].tobytes()
                async with aiofiles.open(codpath, mode="wb") as f:
                  await f.write(jpgdata)
                jsondata = await asyncio.to_thread(json.loads, myzip.read(item + ".json"))
                qs = (trainframe.objects
                  .filter(school=self.myschoolline.id, name=item, deleted=False)
                  .order_by("id"))
                frameline = await qs.afirst()  # erste Zeile (kleinste id)
                if frameline is None:
                  frameline = trainframe(
                    made = timezone.make_aware(datetime.fromtimestamp(time())),
                    school = self.myschoolline.id,
                    name = item,
                    code = jsondata[11],
                    checked = 1,
                    train_status = 0,
                  )
                for j, v in enumerate(jsondata[:10]):
                  setattr(frameline, f"c{j}", v)
                await frameline.asave()
                await sync_to_async(
                  qs.exclude(id=frameline.id).update
                )(deleted=True)
                await frameline.img_sizes.aadd(self.sizeline)
                await frameline.asave()
        await self.send('OK')
        return()
        
      if text_data == 'Ping':
        return()
        
      #logger.info('<-- ' + text_data)
      indict = json.loads(text_data)	
      
      if indict['code'] == 'auth':
        self.myschoolline = await school.objects.aget(id=indict['school'])
        self.mytrainerline = await dbtrainer.objects.aget(
          id = self.myschoolline.trainer_nr
        )
        if self.mytrainerline.t_type == 2:
          if self.ws_session is None:
            import aiohttp
            self.ws_session = aiohttp.ClientSession()
          self.ws = await self.ws_session.ws_connect(
            self.mytrainerline.wsserver + 'ws/remotetrainer/')
          indict['name'] = self.mytrainerline.wsname
          indict['pass'] = self.mytrainerline.wspass
          indict['school'] = self.myschoolline.e_school
          await self.ws.send_str(json.dumps(indict))
          await self.ws.receive()
        else:
          self.user = await User.objects.aget(username=indict['name'])
          self.client_version = indict['version']
          if self.user.check_password(indict['pass']):
            logger.info('Successfull login:' + indict['name'] + ' - Software v' 
                + self.client_version)
            self.authed = True
          if not self.authed:
            logger.info('Login failure: ' + indict['name'])
            await self.close() 
        await self.send(json.dumps('OK'))
          
      elif indict['code'] == 'namecheck':
        if self.mytrainerline.t_type == 2:
          indict['school'] = self.myschoolline.e_school
          await self.ws.send_str(json.dumps(indict))
          while True:
            result = (await self.ws.receive()).data
            await self.send(result)
            if json.loads(result) == 'done':
              break
        else:
          sizeline, _ = await img_size.objects.aget_or_create(
              x=self.myschoolline.model_xin, y=self.myschoolline.model_yin
          )
          query_list = await database_sync_to_async(list)(
            trainframe.objects.filter(
              school=indict['school'],
              deleted=False,
            )
          )
          for item in query_list:
            result = (item.name, seq_to_int((item.c0, item.c1, item.c2, item.c3, 
              item.c4, item.c5, item.c6, item.c7, item.c8, item.c9)),
              await is_size_in_item(item, sizeline))
            await self.send(json.dumps(result)) 
            #logger.info('--> ' + str(result))
          await self.send(json.dumps('done'))
          #logger.info('--> done')
                  
      elif indict['code'] == 'init_trainer':
        if self.mytrainerline.t_type == 2:
          indict['school'] = self.myschoolline.e_school
          await self.ws.send_str(json.dumps(indict))
          await self.send((await self.ws.receive()).data)
        else:
          self.trainer_nr, count = await get_trainer_nr(self.myschoolline)
          self.mytrainerline = await dbtrainer.objects.aget(id = self.trainer_nr)
          creator = await database_sync_to_async(lambda: self.myschoolline.creator)()
          if await afree_quota(creator):
            result = {
              'status' : 'OK',
              'dims' : (self.myschoolline.model_xin, self.myschoolline.model_yin),
            }  
            await self.send(json.dumps(result))
          else: 
            logger.warning('*** User ' + creator.username 
              + ' has no quota for remote training.')
            myfit = fit(school = indict['school'], status = 'NoQuota')
            await myfit.asave()
            result = {
              'status' : 'no_quota',
            }  
            await self.send(json.dumps(result))
            #logger.info('--> ' + str(result))
            await self.close() 
            
      elif indict["code"] == 'set_counter_total':
        if self.mytrainerline.t_type == 2:
          await self.ws.send_str(json.dumps(indict))
          await self.send((await self.ws.receive()).data)
        else:
          counter_dict[self.myschoolline.id] = [indict['action'], indict['count'], 0]
          result = {"status": "OK", }
          #logger.info('--> ' + str(result))
          await self.send(json.dumps(result))
            
      elif indict["code"] == 'set_counter':
        if self.mytrainerline.t_type == 2:
          await self.ws.send_str(json.dumps(indict))
          await self.send((await self.ws.receive()).data)
        else:
          counter_dict[self.myschoolline.id][2] = indict['value']
          result = {"status": "OK", }
          #logger.info('--> ' + str(result))
          await self.send(json.dumps(result))
          
      elif indict["code"] == 'delete':
        if self.mytrainerline.t_type == 2:
          await self.ws.send_str(json.dumps(indict))
          await self.send((await self.ws.receive()).data)
        else:
          qs = trainframe.objects.filter(
            school=self.myschoolline.id,
            name=indict['name'],
            deleted=False,
          )
          @transaction.atomic
          def do_update():
              return qs.update(deleted=True)
          affected = await sync_to_async(do_update)()
          result = {"status": "OK", "deleted": affected, }
          #logger.info('--> ' + str(result))
          await self.send(json.dumps(result))
        
      elif indict['code'] == 'trainnow':
        if self.mytrainerline.t_type == 2:
          await self.ws.send_str(json.dumps(indict))
        else:
          await sync_to_async(self.myschoolline.trainers.add)(self.mytrainerline)
          
      elif indict['code'] == 'checkfitdone':
        if self.mytrainerline.t_type == 2:
          indict['school'] = self.myschoolline.e_school
          await self.ws.send_str(json.dumps(indict))
          result = json.loads((await self.ws.receive()).data)
        else:
          if indict['mode'] == 'init':
            try:    
              fitline = await fit.objects.filter(
                school = self.myschoolline.id
              ).alatest('id')
              self.lastfit = fitline.id
              model_type = self.myschoolline.model_type
            except fit.DoesNotExist:
              self.lastfit = 0
              model_type = default_modeltype
            result = model_type
          elif indict['mode'] == 'sync':
            if 'dl_only' in indict and indict['dl_only']:
              self.lastfit = (await fit.objects.filter(
                school = self.myschoolline.id,
                status = 'Done', 
              ).alatest('id')).id
            else:
              while True:
                try:
                  fitline = (
                    await fit.objects.filter(school = self.myschoolline.id).alatest('id')
                  )  
                  fitline = fitline.id
                except fit.DoesNotExist:
                  fitline = 0
                if fitline > self.lastfit:
                  self.lastfit = fitline
                  break
                else:
                  await asyncio.sleep(1.0)
            mytoken = await maketoken_async(
              'MOD', self.myschoolline.id, 
              'Download School #'+str(self.myschoolline.id)
            )
            dlurl = settings.CLIENT_URL
            dlurl += 'trainers/downmodel/'
            dlurl += str(self.myschoolline.id) + '/' + str(mytoken[0])
            dlurl += '/' + mytoken[1] +'/'
            if version_newer_or_equal(self.client_version, '1.8.8b'):
              result = {'dl_url' : dlurl, 'fit_nr' : self.lastfit, } 
            else:  
              result = dlurl
          elif indict['mode'] == 'check': #obsolete if all clients are beyond v1.8.8a
            fitline = await fit.objects.aget(id=self.lastfit)
            result = fitline.status == 'Done' 
        #logger.info('--> ' + str(result))
        await self.send(json.dumps(result))	
          
      elif indict['code'] == 'close_ws':
        await self.send(json.dumps('OK'))	
        if self.ws_session is not None:
          #await asyncio.sleep(1.0)  
          await self.ws_session.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (remotetrainer)')
      logger.error(format_exc())

#*****************************************************************************
# TrainerUtil
#*****************************************************************************

class trainerutil(AsyncWebsocketConsumer):

  async def send_ping(self):
    if self.ws_ts is None:
      return()
    if (time() - self.ws_ts) > 9:
      while True:
        try:
          self.ws.send('Ping', opcode=1)
          self.ws_ts = time()
          break
        except BrokenPipeError:
          self.logger.warning('Socket error while pinging training server')
          sleep(medium_brake)

  async def connect(self):
    try:
      self.ws_ts = None
      self.status_string = 'Idle'
      await self.accept()
      self.trainer_nr = None
      self.ws_session = None
      self.list_of_dicts = []
      
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())

  async def disconnect(self, code):
    try:
      if self.ws_session is not None:
        await self.ws_session.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())

  async def receive(self, text_data):
    try:
      if text_data == 'Ping':
        return()
      #logger.info('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}							

      if params['command'] == 'connecttrainer':
        self.schoolnr = params['school']
        if self.scope['user'].is_authenticated:
          myuser = self.scope['user']
        else:
          myuser = await User.objects.aget(username=params['name'])
          if await database_sync_to_async(myuser.check_password)(params['pass']):
            self.authed = True
          if not self.authed:
            await self.close() 
        if await access.check_async('S', self.schoolnr, myuser, 'R'):
          self.maywrite = await access.check_async('S', self.schoolnr, myuser, 'W')
          self.schoolline = await school.objects.aget(id=self.schoolnr)
          self.trainer_nr, count = await get_trainer_nr(self.schoolline)
          self.trainerline = await dbtrainer.objects.aget(id = self.trainer_nr)
          #self.client_version = params['version']
          if self.trainerline.t_type == 2:
            if self.ws_session is None:
              import aiohttp
              self.ws_session = aiohttp.ClientSession()
            self.ws = await self.ws_session.ws_connect(
              self.trainerline.wsserver + 'ws/trainerutil/')
            self.ws_ts = time()
            temp = json.loads(text_data)
            temp['data']['school']=self.schoolline.e_school
            temp['data']['name']=self.trainerline.wsname
            temp['data']['pass']=self.trainerline.wspass
            await self.ws.send_str(json.dumps(temp))
            returned = await self.ws.receive() 
            result = json.loads(returned.data)['data']
            if result == 'OK' or ('status' in result and result['status'] == 'OK'):
              result['t_type'] = self.trainerline.t_type
              outlist['data'] = result  
            else:
              await self.close()	
              return()
          else:  
            outlist['data'] = {
              'status' : 'OK',
              'trainer' : self.trainer_nr,
              'count' : count,
              't_type' : self.trainerline.t_type,
            }
        else: #Proper error description to both consoles!!!
          await self.close()
          return()
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))			

      elif params['command'] == 'getschoolinfo':
        countlist1 = trainframe.objects.filter(school=params['school'])
        infolocal = {}
        infolocal['nr_total'] = await countlist1.acount()
        countlist = countlist1.filter(checked=True)
        infolocal['nr_checked'] = await countlist.acount()
        infolocal['nr_trained'] = await countlist.filter(code='TR').acount()
        infolocal['nr_validated'] = await countlist.filter(code='VA').acount()
        infolocal['nr_not_trained'] = await countlist.filter(train_status__lt=2).acount()
        infolocal['nr_not_checked'] = infolocal['nr_total'] - infolocal['nr_checked']
        infolocal['recog0'] = await countlist1.filter(c0=1).acount()
        infolocal['recog1'] = await countlist1.filter(c1=1).acount()
        infolocal['recog2'] = await countlist1.filter(c2=1).acount()
        infolocal['recog3'] = await countlist1.filter(c3=1).acount()
        infolocal['recog4'] = await countlist1.filter(c4=1).acount()
        infolocal['recog5'] = await countlist1.filter(c5=1).acount()
        infolocal['recog6'] = await countlist1.filter(c6=1).acount()
        infolocal['recog7'] = await countlist1.filter(c7=1).acount()
        infolocal['recog8'] = await countlist1.filter(c8=1).acount()
        infolocal['recog9'] = await countlist1.filter(c9=1).acount()
        if self.trainerline.t_type == 2:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          inforemote = json.loads(returned.data)['data']
          infolocal['nr_trained'] = inforemote['nr_trained']
          infolocal['nr_validated'] = inforemote['nr_validated']
        outlist['data'] = infolocal
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))				

      elif params['command'] == 'getfitinfo':
        if self.trainerline.t_type == 2:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          datatemp = json.loads(returned.data)['data']
          outlist['data'] = datatemp 
        else:
          query_set = fit.objects.filter(school=params['school'])
          i = 0
          result = [] 
          async for item in query_set:
            fit_dict = model_to_dict(item)
            fit_dict['nr'] = i
            fit_dict['made'] = item.made.strftime("%Y-%m-%d")
            if len(self.list_of_dicts) <= i or fit_dict != self.list_of_dicts[i]:
              if len(self.list_of_dicts) > i:
                self.list_of_dicts[i] = fit_dict
              else:  
                self.list_of_dicts.append(fit_dict)
              result.append(fit_dict)
            i += 1  
          outlist['data'] = result
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'getepochsinfo':
        if self.trainerline.t_type == 2:
          temp = json.loads(text_data)
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else:
          result = []
          async for item in epoch.objects.filter(fit=params['fitnr']):
            result.append({
              'phase' : item.phase,
              'loss' : item.loss, 
              'augmentation' : item.augmentation, 
              'gamma' : item.gamma, 
              'binacc' : item.binacc, 
              'recall' : item.recall, 
              'precision' : item.precision, 
              'val_loss' : item.val_loss, 
              'val_binacc' : item.val_binacc, 
              'val_recall' : item.val_recall, 
              'val_precision' : item.val_precision, 
              'seconds' : item.seconds, 
              'learning_rate' : item.learning_rate,
            })
          outlist['data'] = result
      
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))								

      elif params['command'] == 'getparams':
        if self.trainerline.t_type == 2:
          await self.ws.send_str(text_data)
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else:
          line = await fit.objects.aget(id=params['fitnr'])
          result = {
            'model_type' : line.model_type, 
            'model_image_augmentation' : line.model_image_augmentation, 
            'model_gamma' : line.model_gamma, 
            'model_finetuning' : line.model_finetuning, 
            'l_rate_min' : line.l_rate_min, 
            'l_rate_max' : line.l_rate_max, 
            'l_rate_target' : line.l_rate_target, 
            'early_stop_patience' : line.early_stop_patience,
          } 
            
          outlist['data'] = result
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))				

      elif params['command'] == 'getqueueinfo':
        if self.trainerline.t_type == 2:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else:
          joblist = trainers[self.trainer_nr].getqueueinfo()
          try:
            outlist['data'] = {'pos' : joblist.index(self.schoolnr) + 1, 
              'len' : len(joblist), }
          except ValueError:
            outlist['data'] = {'pos' : 0, 'len' : len(joblist), }
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))		

      elif params['command'] == 'trainnow': 
        if not self.maywrite:
          self.close()	
        schoolline = await school.objects.aget(id=self.schoolnr)
        await sync_to_async(schoolline.trainers.add)(self.trainerline)
        outlist['data'] = 'OK' 
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	

      elif params['command'] == 'dl_only': 
        if not self.maywrite:
          self.close()	
        my_trainer = train_once_remote(
            myschool = await school.objects.aget(id=self.schoolnr), 
            dbline = self.trainerline,
            dl_only = True,
        )
        train_process = Process(target = my_trainer.run)
        train_process.start()
        try:
          await asyncio.wait_for(asyncio.to_thread(train_process.join), timeout=120.0)
        except asyncio.TimeoutError:
          logging.warning("Trainer-Process timeout → terminate()")
          train_process.terminate()
          await asyncio.to_thread(train_process.join)
        rc = train_process.exitcode
        if rc == 0:
          outlist['data'] = 'OK' 
        else:
          outlist['data'] = f'FAILED (exitcode={rc})'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
          
      elif params['command'] == 'get_for_dashboard':  	
        if self.trainerline.t_type == 2:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          answer = json.loads(returned.data)['data']
          schoolline = await school.objects.aget(id=self.schoolnr)
          setattr(schoolline, params['item'], answer)
          try:
            await schoolline.asave(update_fields=[params['item']])
          except ValueError:
            logger.warning('Old table version: Better update your client software') 
          outlist['data'] = answer
        else:  
          schoolline = await school.objects.aget(id=self.schoolnr)
          try:
            outlist['data'] = getattr(schoolline, params['item'])
          except AttributeError:
            outlist['data'] = 0
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))						

      elif params['command'] == 'set_from_dashboard':
        if self.maywrite:
          schoolline = await school.objects.aget(id = self.schoolnr)
          setattr(schoolline, params['item'], params['value'])
          await schoolline.asave(update_fields = [params['item']])
          if self.trainerline.t_type == 2:
            temp = json.loads(text_data)
            temp['data']['school']=self.schoolline.e_school
            await self.ws.send_str(json.dumps(temp))
            returned = await self.ws.receive()
            if json.loads(returned.data)['data'] != 'OK':
              self.close()	
          if params['item'] == 'model_type':
            schoolline.last_fit += 1
            await schoolline.asave(update_fields=('last_fit', ))
          outlist['data'] = 'OK'
          #logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	
        else:
          self.close()						

      elif params['command'] == 'getavailmodels':
        if self.trainerline.t_type == 2:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else: 
          modeldir = self.schoolline.dir
          outlist['data'] = []
          model_type_lines = model_type.objects.all()
          async for item in  model_type_lines:
            search_path = modeldir + 'model/' + item.name
            if await aiofiles.os.path.exists(search_path + '.keras'):
              outlist['data'].append(item.name)
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
      elif params['command'] == 'get_count':
        if self.trainerline.t_type == 2:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else: 
          try:
            outlist['data'] = counter_dict[self.schoolline.id]
          except KeyError:
            outlist['data'] = ('?', 0, 0)
          #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
        
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())
