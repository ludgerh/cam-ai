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
from os import path, makedirs
from math import inf
from time import time, sleep
from datetime import datetime
from logging import getLogger
from traceback import format_exc
from zipfile import ZipFile
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from django.forms.models import model_to_dict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from camai.version import version
from tools.l_tools import (
  djconf, 
  seq_to_int, 
  version_newer_or_equal, 
  version_older_or_equal,
)
from tools.c_logger import log_ini
from access.c_access import access
from tools.tokens import maketoken_async
from tf_workers.models import school
from users.userinfo import afree_quota
from .models import trainframe, fit, epoch, trainer as dbtrainer, img_size, model_type
from globals.c_globals import trainers

from random import randint

logname = 'ws_trainers'
logger = getLogger(logname)
log_ini(logger, logname)
default_modeltype = djconf.getconfig('default_modeltype', 'efficientnetv2-b0')
medium_brake = djconf.getconfigfloat('medium_brake', 0.1)

async def get_trainer_nr(school_line):
  trainerlist = []
  async for item in school_line.trainers.filter(active = True):
    trainerlist.append(item)  
  if len(trainerlist) == 1:    
    result = trainerlist[0].id
  else:  
    result = -1
    length = inf
    for item in trainerlist:   
      joblist = trainers[item.id].getqueueinfo() 
      if school_line.id in joblist:
        result = item.id
        break
      if len(joblist) < length:
        length = len(joblist)
        result = item.id
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
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (remotetrainer)')
      logger.error(format_exc())

  async def receive(self, text_data =None, bytes_data=None):
    try:
      if bytes_data: 
        #logger.info('<-- binary')
        cod_x = self.myschoolline.model_xin
        cod_y = self.myschoolline.model_yin
        ram_file = io.BytesIO(bytes_data)
        if self.mytrainerline.t_type in {2, 3}:
          zip_buffer = io.BytesIO()  
          zip_content = ram_file.read()
          await self.ws.send_bytes(zip_content)
          await self.ws.receive()
        else:
          with ZipFile(ram_file) as myzip:
            i = len(myzip.namelist())
            for item in myzip.namelist():
              logger.info('(' +str(i)+ ') Unpacking: ' + item)
              i -= 1
              if item[-4:] == '.bmp':
                codpath = (self.myschoolline.dir
                  + 'coded/' + str(cod_x) + 'x' + str(cod_y) 
                  + '/' + item[:-4] + '.cod')
                mydir = path.dirname(codpath) 
                if not await aiofiles.os.path.exists(mydir):
                  makedirs(mydir)
                jpgdata = myzip.read(item)
                imgdata = cv.imdecode(np.frombuffer(
                  jpgdata, dtype=np.uint8), cv.IMREAD_COLOR)
                if (imgdata.shape[1] != cod_x or  imgdata.shape[0] != cod_y):
                  imgdata = cv.resize(imgdata, (cod_x, cod_y))
                  imgdata = cv.imencode('.jpg', imgdata)[1].tobytes()
                  async with aiofiles.open(codpath, mode="wb") as f:
                    await f.write(imgdata)
                else:
                  async with aiofiles.open(codpath, mode="wb") as f:
                    await f.write(jpgdata)
                jsondata = json.loads(myzip.read(item + '.json'))  
                try:  
                  frameline = await trainframe.objects.aget(
                    name=item, 
                    school=self.myschoolline.id,
                  )
                except trainframe.DoesNotExist:  
                  frameline = trainframe(
                    made = timezone.make_aware(datetime.fromtimestamp(time())),
                    school = self.myschoolline.id,
                    name = item,
                    code = jsondata[11],
                    c0 = jsondata[0], c1 = jsondata[1], c2 = jsondata[2], c3 = jsondata[3],
                    c4 = jsondata[4], c5 = jsondata[5], c6 = jsondata[6], c7 = jsondata[7],
                    c8 = jsondata[8], c9 = jsondata[9],
                    checked = 1,
                    train_status = 0,
                  )
                  await frameline.asave()
                try:
                  sizeline = await img_size.objects.aget(x=cod_x, y=cod_y)
                except img_size.DoesNotExist:
                  sizeline = img_size(x=cod_x, y=cod_y)
                  await sizeline.asave()
                await frameline.img_sizes.aadd(sizeline)
                await frameline.asave()
        await self.send('OK')
        return()
        
      if text_data == 'Ping':
        return()
        
      #logger.info('<-- ' + text_data)
      indict = json.loads(text_data)	
      
      if indict['code'] == 'auth':
        self.myschoolline = await school.objects.aget(id=indict['school'])
        t_query = self.myschoolline.trainers.filter(active = True)
        self.mytrainerline = await t_query.afirst()
        if self.mytrainerline.t_type in {2, 3}:
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
          if 'version' in indict:
            in_version = indict['version']
          else:
            in_version = '?'
          if self.user.check_password(indict['pass']):
            logger.info('Successfull login:' + indict['name'] + ' - Software v' 
                + in_version)
            self.authed = True
          if not self.authed:
            logger.info('Login failure: ' + indict['name'])
            await self.close() 
        await self.send(json.dumps('OK'))
          
      elif indict['code'] == 'namecheck':
        if self.mytrainerline.t_type in {2, 3}:
          indict['school'] = self.myschoolline.e_school
          await self.ws.send_str(json.dumps(indict))
          while True:
            result = await self.ws.receive()
            result = result.data
            result = json.loads(result)
            await self.send(json.dumps(result))
            if result == 'done':
              break
        else:
          try:
            sizeline = await img_size.objects.aget(x=self.myschoolline.model_xin,
              y=self.myschoolline.model_yin)
          except img_size.DoesNotExist:
            sizeline = img_size(x=self.myschoolline.model_xin,
              y=self.myschoolline.model_yin)
            await sizeline.asave()
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
          await self.send(json.dumps('done'))
                  
      elif indict['code'] == 'init_trainer':
        if self.mytrainerline.t_type in {2, 3}:
          indict['school'] = self.myschoolline.e_school
          await self.ws.send_str(json.dumps(indict))
          result = await self.ws.receive()
          result = json.loads(result.data)
          await self.send(json.dumps(result))
        else:
          if 'version' in indict and version_newer_or_equal(indict['version'], '1.6.2b'):
            self.trainer_nr, count = await get_trainer_nr(self.myschoolline)
          else:
            self.trainer_nr = 1  
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
            await self.close() 
        
      elif indict['code'] == 'delete':
        if self.mytrainerline.t_type in {2, 3}:
          await self.ws.send_str(json.dumps(indict))
          result = await self.ws.receive()
          await self.send(result.data)
        else:
          frameline = await trainframe.objects.aget(
            name=indict['name'], 
            school=self.myschoolline.id,
          )
          frameline.deleted = True
          await frameline.asave(update_fields=('deleted', ))
          await self.send('OK')
        
      elif indict['code'] == 'trainnow':
        if self.mytrainerline.t_type in {2, 3}:
          await self.ws.send_str(json.dumps(indict))
        else:
          self.myschoolline.trainer_nr = self.trainer_nr
          await self.myschoolline.asave(update_fields=['trainer_nr'])
          
      elif indict['code'] == 'checkfitdone':
        if self.mytrainerline.t_type in {2, 3}:
          indict['school'] = self.myschoolline.e_school
          await self.ws.send_str(json.dumps(indict))
          result = await self.ws.receive()
          result = json.loads(result.data)
        else:
          if indict['mode'] == 'init':
            try:    
              fitline = await fit.objects.filter(school=self.myschoolline.id).alatest('id')
              self.lastfit = fitline.id
              model_type = self.myschoolline.model_type
            except fit.DoesNotExist:
              self.lastfit = 0
              model_type = default_modeltype
            result = model_type
          elif indict['mode'] == 'sync':
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
            result = dlurl
          elif indict['mode'] == 'check':
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

  async def disconnect(self, code):
    try:
      logger.debug('Disconnected, Code:'+ str(code))
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
      self.query_count = 0
      self.query_working = False
      self.ws_session = None
      self.new_click = False
      
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
          if 'version' in params:
            self.version = params['version']
          else:
            self.version = '0.0.0'  
          if self.trainerline.t_type in {2, 3}:
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
              outlist['data'] = result  
            else:
              await self.close()	
              return()
          else:  
            if version_newer_or_equal(self.version, '1.6.2b'):
              outlist['data'] = {
                'status' : 'OK',
                'trainer' : self.trainer_nr,
                'count' : count,
              }
            else:  
              self.trainer_nr = 1
              outlist['data'] = 'OK'  
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
        if self.trainerline.t_type in {2, 3}:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          inforemote = json.loads(returned.data)['data']
          infolocal['nr_trained'] = inforemote['nr_trained']
          infolocal['nr_validated'] = inforemote['nr_validated']
        outlist['data'] = infolocal
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))				

      elif params['command'] == 'getfitinfo':
        if self.trainerline.t_type in {2, 3}:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          datatemp = json.loads(returned.data)['data']
          if version_older_or_equal(self.version, '1.6.6'):
            for item in datatemp[0]:
              item['l_rate_patience'] = 0
              item['l_rate_delta_min'] = 0
              item['l_rate_decrement'] = 0
          outlist['data'] = datatemp 
        else:
          if 'new_click' in params and params['new_click']:
            self.new_click = True
          all_fits = fit.objects.filter(school=params['school'])
          last_fit = await fit.objects.filter(school=params['school']).alast()
          temp_count = await all_fits.acount()
          result = [] 
          if temp_count:
            if self.query_working:
              query_set = all_fits[self.query_count - 1:] 
              new_epoch = False
              remove = True
            else:
              query_set = all_fits[self.query_count:] 
              new_epoch = self.query_count < temp_count
              self.query_count = temp_count
              remove = False
            if last_fit.status in {'Working', 'Queuing'}: 
              self.new_click = False
              self.status_string = last_fit.status  
              self.query_working = True
            else:  
              if self.new_click:
                self.status_string = 'Preparing'  
              else:
                self.status_string = 'Idle'  
              self.query_working = False
            async for item in query_set:
              fit_dict = model_to_dict(item)
              fit_dict['made'] = item.made.strftime("%Y-%m-%d")
              result.append(fit_dict)
          else:
            remove = 0
            new_epoch = False
          outlist['data'] = (result, remove, new_epoch, self.status_string)
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'getepochsinfo':
        if self.trainerline.t_type in {2, 3}:
          temp = json.loads(text_data)
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else:
          result = []
          async for item in epoch.objects.filter(fit=params['fitnr']):
            result.append({
              'loss':item.loss, 
              'binacc':item.binacc, 
              'auc':item.auc, 
              'val_loss':item.val_loss, 
              'val_binacc':item.val_binacc, 
              'val_auc':item.val_auc, 
              'seconds':item.seconds, 
              'learning_rate':item.learning_rate,
            })
          outlist['data'] = result
      
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))								

      elif params['command'] == 'getparams':
        if self.trainerline.t_type in {2, 3}:
          await self.ws.send_str(text_data)
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else:
          line = await fit.objects.aget(id=params['fitnr'])
          result = {
            'model_type':line.model_type, 
            'model_image_augmentation':line.model_image_augmentation, 
            'model_weight_decay':line.model_weight_decay, 
            'model_weight_constraint':line.model_weight_constraint, 
            'model_dropout':line.model_dropout, 
            'l_rate_start':line.l_rate_start, 
            'l_rate_stop':line.l_rate_stop, 
            'l_rate_divisor':line.l_rate_divisor, 
            'weight_min':line.weight_min, 
            'weight_max':line.weight_max, 
            'weight_boost':line.weight_boost, 
            'early_stop_delta_min':line.early_stop_delta_min, 
            'early_stop_patience':line.early_stop_patience,
          } 
            
          outlist['data'] = result
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))				

      elif params['command'] == 'getqueueinfo':
        if self.trainerline.t_type in {2, 3}:
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
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))		

      elif params['command'] == 'trainnow': 
        if self.maywrite:
          schoolline = await school.objects.aget(id=self.schoolnr)
          schoolline.trainer_nr = self.trainer_nr
          await schoolline.asave(update_fields=['trainer_nr'])
          outlist['data'] = 'OK' 
          #logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	
        else:
          self.close()		
          
      elif params['command'] == 'get_for_dashboard':  	
        if self.trainerline.t_type in {2, 3}:
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
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))						

      elif params['command'] == 'set_from_dashboard':
        if self.maywrite:
          schoolline = await school.objects.aget(id=self.schoolnr)
          setattr(schoolline, params['item'], params['value'])
          await schoolline.asave(update_fields=[params['item']])
          if self.trainerline.t_type in {2, 3}:
            temp = json.loads(text_data)
            temp['data']['school']=self.schoolline.e_school
            await self.ws.send_str(json.dumps(temp))
            returned = await self.ws.receive()
            if json.loads(returned.data)['data'] != 'OK':
              self.close()	
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	
        else:
          self.close()						

      elif params['command'] == 'getavailmodels':
        if self.trainerline.t_type == 3:
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
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())
