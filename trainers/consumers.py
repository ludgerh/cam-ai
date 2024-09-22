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
import cv2 as cv
import numpy as np
import asyncio
import aiofiles
import aiofiles.os
import io
from os import path, makedirs
from time import time, sleep
from datetime import datetime
from logging import getLogger
from traceback import format_exc
from asgiref.sync import sync_to_async
from zipfile import ZipFile
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tools.l_tools import djconf, seq_to_int
from tools.c_logger import log_ini
from access.c_access import access
from tools.tokens import maketoken_async
from tf_workers.models import school, worker
from users.userinfo import afree_quota
from .models import trainframe, fit, epoch, trainer as dbtrainer, img_size, model_type
from .c_trainers import trainers

logname = 'ws_trainers'
logger = getLogger(logname)
log_ini(logger, logname)
default_modeltype = djconf.getconfig('default_modeltype', 'efficientnetv2-b0')
medium_brake = djconf.getconfigfloat('medium_brake', 0.1)

#*****************************************************************************
# RemoteTrainer
#*****************************************************************************

class remotetrainer(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      self.frameinfo = {}
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (remotetrainer)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def receive(self, text_data =None, bytes_data=None):
    try:
      if bytes_data: 
        cod_x = self.myschoolline.model_xin
        cod_y = self.myschoolline.model_yin
        ram_file = io.BytesIO(bytes_data)
        with ZipFile(ram_file) as myzip:
          for item in myzip.namelist():
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
                  train_status = 1,
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
        self.user = await User.objects.aget(username=indict['name'])
        if self.user.check_password(indict['pass']):
          logger.info('Successfull login:' + indict['name'])
          self.authed = True
        if not self.authed:
          logger.info('Login failure: ' + indict['name'])
          await self.close() 
        await self.send(json.dumps('OK'))
          
      elif indict['code'] == 'namecheck':
        try:
          sizeline = await img_size.objects.aget(x=self.myschoolline.model_xin,
            y=self.myschoolline.model_yin)
        except img_size.DoesNotExist:
          sizeline = img_size(x=self.myschoolline.model_xin,
            y=self.myschoolline.model_yin)
          await sizeline.asave()
        result = []
        query_list = await database_sync_to_async(list)(trainframe.objects.filter(
          school=indict['school'],
          img_sizes=sizeline,
          deleted=False,
        ))
        for item in query_list:
          result.append((item.name, seq_to_int((item.c0, item.c1, item.c2, item.c3, 
            item.c4, item.c5, item.c6, item.c7, item.c8, item.c9))))
        await self.send(json.dumps(result))
        
      elif indict['code'] == 'init_trainer':
        self.myschoolline = await school.objects.aget(id=indict['school'])
        creator = await sync_to_async(lambda: self.myschoolline.creator)()
        if await afree_quota(creator):
          result = {
            'status' : 'OK',
            'dims' : (self.myschoolline.model_xin, self.myschoolline.model_yin),
          }  
          await self.send(json.dumps(result))
        else: 
          logger.warning('*** User ' + creator.username 
            + ' has no quota for remote training.')
          myfit = fit(school = indict['school'])
          myfit.status = 'NoQuota'
          await myfit.asave()
          result = {
            'status' : 'no_quota',
          }  
          await self.send(json.dumps(result))
          await self.close() 
        
      elif indict['code'] == 'send':
        self.frameinfo['name'] = indict['name']
        self.frameinfo['tags'] = indict['tags']
        self.frameinfo['code'] = indict['framecode']
        
      elif indict['code'] == 'delete':
        frameline = await trainframe.objects.aget(name=indict['name'])
        bmppath = self.myschoolline.dir + 'frames/' + indict['name']
        await frameline.adelete()
        if await aiofiles.os.path.exists(bmppath):
          await aiofiles.os.remove(bmppath)
        codpath = (self.myschoolline.dir
          + 'coded/' 
          + str(self.myschoolline.model_xin) 
          + 'x' + str(self.myschoolline.model_yin) 
          + '/' + indict['name'][:-4]+'.cod')
        if await aiofiles.os.path.exists(codpath):
          await aiofiles.os.remove(codpath)
        await self.send('OK')
        
      elif indict['code'] == 'trainnow':
        schoolline = await school.objects.aget(id=self.myschoolline.id)
        schoolline.extra_runs = 1
        await schoolline.asave(update_fields=['extra_runs'])
          
      elif indict['code'] == 'checkfitdone':
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
          result = fitline.status =='Done' 
        logger.debug('--> ' + str(result))
        await self.send(json.dumps(result))	
    except:
      logger.error('Error in consumer: ' + logname + ' (remotetrainer)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def disconnect(self, code):
    try:
      logger.debug('Disconnected, Code:'+ str(code))
    except:
      logger.error('Error in consumer: ' + logname + ' (remotetrainer)')
      logger.error(format_exc())
      logger.handlers.clear()

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
      await self.accept()
      self.trainernr = None
      self.query_count = 0
      self.query_working = False
      self.ws_session = None
      
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def disconnect(self, code):
    try:
      if self.trainernr is not None:
        if self.didrunout:
          trainers[self.trainernr].stop_out(self.schoolnr)
        if self.ws_session is not None:
          await self.ws_session.close()
      logger.debug('Disconnected, Code:'+ str(code))
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def receive(self, text_data):
    try:
      if text_data == 'Ping':
        return()
      logger.debug('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

      if params['command'] == 'getschoolinfo':
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
          outlist['data'] = json.loads(returned.data)['data']
        else:
          all_fits = fit.objects.filter(school=params['school'])
          last_fit = await all_fits.alast()
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
              unshow_modal = not self.query_working
              self.query_working = True
            else:  
              unshow_modal = False
              self.query_working = False
            async for item in query_set:
              if item.status == 'NoQuota':
                unshow_modal = True
              result.append({
                'id':item.id, 'made':item.made.strftime("%Y-%m-%d"), 
                'nr_tr':item.nr_tr, 'nr_va':item.nr_va, 'minutes':item.minutes, 
                'epochs':item.epochs, 'loss':item.loss, 'cmetrics':item.cmetrics, 
                'val_loss':item.val_loss, 'val_cmetrics':item.val_cmetrics, 
                'hit100':item.hit100, 'val_hit100':item.val_hit100, 'status':item.status, 
                'model_type':item.model_type, 
                'model_image_augmentation':item.model_image_augmentation, 
                'model_weight_decay':item.model_weight_decay,
                'model_weight_constraint':item.model_weight_constraint, 
                'model_dropout':item.model_dropout, 'l_rate_start':item.l_rate_start, 
                'l_rate_stop':item.l_rate_stop, 'l_rate_delta_min':item.l_rate_delta_min, 
                'l_rate_patience':item.l_rate_patience, 
                'l_rate_decrement':item.l_rate_decrement, 'weight_min':item.weight_min, 
                'weight_max':item.weight_max, 'weight_boost':item.weight_boost, 
                'early_stop_delta_min':item.early_stop_delta_min, 
                'early_stop_patience':item.early_stop_patience,
              })
          else:
            remove = 0
            new_epoch = False
            unshow_modal = False
          outlist['data'] = (result, remove, new_epoch, unshow_modal)
        logger.debug('--> ' + str(outlist))
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
              'loss':item.loss, 'cmetrics':item.cmetrics, 'val_loss':item.val_loss, 
              'val_cmetrics':item.val_cmetrics, 'hit100':item.hit100, 
              'val_hit100':item.val_hit100, 'seconds':item.seconds, 
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
            'model_dropout':line.model_dropout, 'l_rate_start':line.l_rate_start, 
            'l_rate_stop':line.l_rate_stop, 'l_rate_delta_min':line.l_rate_delta_min, 
            'l_rate_patience':line.l_rate_patience, 
            'l_rate_decrement':line.l_rate_decrement, 'weight_min':line.weight_min, 
            'weight_max':line.weight_max, 'weight_boost':line.weight_boost, 
            'early_stop_delta_min':line.early_stop_delta_min, 
            'early_stop_patience':line.early_stop_patience,
          } 
            
          outlist['data'] = result
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))							

      elif params['command'] == 'connecttrainer':
        self.schoolnr = params['school']
        if self.scope['user'].is_authenticated:
          myuser = self.scope['user']
        else:
          myuser = await User.objects.aget(username=params['name'])
          if myuser.check_password(params['pass']):
            self.authed = True
          if not self.authed:
            await self.close() 
        if await access.check_async('S', self.schoolnr, myuser, 'R'):
          self.maywrite = await access.check_async('S', self.schoolnr, myuser, 'W')
          self.schoolline = await school.objects.aget(id=self.schoolnr)
          tf_workerline = await worker.objects.aget(school__id=self.schoolnr)
          self.trainerline = await dbtrainer.objects.aget(school__id=self.schoolnr)
          self.trainernr = self.trainerline.id
          if self.trainerline.t_type in {2, 3}:
            if self.ws_session is None:
              import aiohttp
              self.ws_session = aiohttp.ClientSession()
            self.ws = await self.ws_session.ws_connect(
              self.trainerline.wsserver + 'ws/trainerutil/')
            self.ws_ts = time()
            temp = json.loads(text_data)
            temp['data']['school']=self.schoolline.e_school
            temp['data']['name']=tf_workerline.wsname
            temp['data']['pass']=tf_workerline.wspass
            temp['data']['dorunout']=params['dorunout']
            await self.ws.send_str(json.dumps(temp))
            returned = await self.ws.receive() 
            if json.loads(returned.data)['data'] != 'OK':
              await self.close()	
        else: #Proper error description to both consoles!!!
          await self.close()
        if params['dorunout']:
          outlist['data'] = trainers[self.trainernr].run_out(self.schoolnr)
          self.didrunout = True
        else:
          outlist['data'] = 'OK'
          self.didrunout = False
        if outlist['data'] == 'Busy':
          self.trainernr = None
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))						

      elif params['command'] == 'getqueueinfo':
        if self.trainerline.t_type in {2, 3}:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoolline.e_school
          await self.ws.send_str(json.dumps(temp))
          returned = await self.ws.receive()
          outlist['data'] = json.loads(returned.data)['data']
        else:
          if 'school' in params:
            joblist = trainers[self.trainernr].getqueueinfo(params['school'])
          else:
            joblist = trainers[self.trainernr].getqueueinfo(self.schoolnr)
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
          schoolline.extra_runs = 1
          await schoolline.asave(update_fields=['extra_runs'])
          outlist['data'] = 'OK' 
          logger.debug('--> ' + str(outlist))
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
          await schoolline.asave(update_fields=[params['item']])
          outlist['data'] = answer
        else:  
          schoolline = await school.objects.aget(id=self.schoolnr)
          outlist['data'] = getattr(schoolline, params['item'])
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
            if await aiofiles.os.path.exists(search_path + '.h5'):
              outlist['data'].append(item.name)
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())
      logger.handlers.clear()		

