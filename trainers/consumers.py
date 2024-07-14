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
from os import remove, path, makedirs, rename
from time import time, sleep
from datetime import datetime
from logging import getLogger
from traceback import format_exc
from django.core import serializers
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tools.l_tools import djconf, seq_to_int
from tools.c_logger import log_ini
from tools.djangodbasync import (getonelinedict, updatefilter, getoneline, 
  filterlinesdict, savedbline, deletefilter)
from access.c_access import access
from tools.tokens import maketoken_async
from tf_workers.models import school, worker
from .models import trainframe, fit, epoch, trainer as dbtrainer, img_size, model_type
from .c_trainers import trainers

logname = 'ws_trainerconsumers'
logger = getLogger(logname)
log_ini(logger, logname)
default_modeltype = djconf.getconfig('default_modeltype', 'efficientnetv2-b0')
medium_brake = djconf.getconfigfloat('medium_brake', 0.1)

#*****************************************************************************
# RemoteTrainer
#*****************************************************************************

class remotetrainer(AsyncWebsocketConsumer):

  async def connect(self):
    self.frameinfo = {}
    await self.accept()

  async def receive(self, text_data =None, bytes_data=None):
    if bytes_data: 
      cod_x = self.myschoolline.model_xin
      cod_y = self.myschoolline.model_yin
      filepath = (self.myschoolline.dir
        + 'coded/' + str(cod_x) + 'x' + str(cod_y) 
        + '/' + self.frameinfo['name'][:-4]+'.jpg')
      codpath = filepath[:-4]+'.cod'
      mydir = path.dirname(filepath) 
      if not await aiofiles.os.path.exists(mydir):
        makedirs(mydir)
      imgdata = cv.imdecode(np.frombuffer(bytes_data, dtype=np.uint8), (cv.IMREAD_COLOR))
      if (imgdata.shape[1] != cod_x or  imgdata.shape[0] != cod_y):
        imgdata = cv.resize(imgdata, (cod_x, cod_y))
        imgdata = cv.imencode('.jpg', imgdata)[1].tobytes()
        async with aiofiles.open(codpath, mode="wb") as f:
          await f.write(imgdata)
      else:
        async with aiofiles.open(codpath, mode="wb") as f:
          await f.write(bytes_data)
      try:  
        frameline = await trainframe.objects.aget(
          name=self.frameinfo['name'], 
          school=self.myschoolline.id,
        )
      except trainframe.DoesNotExist:  
        frameline = trainframe(
          made = timezone.make_aware(datetime.fromtimestamp(time())),
          school = self.myschoolline.id,
          name = self.frameinfo['name'],
          code = self.frameinfo['code'],
          c0 = self.frameinfo['tags'][0], c1 = self.frameinfo['tags'][1],
          c2 = self.frameinfo['tags'][2], c3 = self.frameinfo['tags'][3],
          c4 = self.frameinfo['tags'][4], c5 = self.frameinfo['tags'][5],
          c6 = self.frameinfo['tags'][6], c7 = self.frameinfo['tags'][7],
          c8 = self.frameinfo['tags'][8], c9 = self.frameinfo['tags'][9],
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
      
    logger.debug('<-- ' + text_data)
    indict = json.loads(text_data)	
    
    if indict['code'] == 'auth':
      self.user = await User.objects.aget(username=indict['name'])
      if self.user.check_password(indict['pass']):
        logger.info('Successfull login:' + indict['name'])
        self.authed = True
      if not self.authed:
        logger.info('Login failure: ' + indict['name'])
        await self.close() 
        
    elif indict['code'] == 'namecheck':
      try:
        sizeline = await img_size.objects.aget(x=self.myschoolline.model_xin,
          y=self.myschoolline.model_yin)
      except img_size.DoesNotExist:
        sizeline = img_size(x=self.myschoolline.model_xin,
          y=self.myschoolline.model_yin)
        await sizeline.asave()
      async for item in trainframe.objects.filter(
        school=indict['school'],
        img_sizes=sizeline,
      ):
        result =  (item.name, seq_to_int((item.c0, item.c1, item.c2, item.c3, item.c4, 
          item.c5, item.c6, item.c7, item.c8, item.c9)))
        await self.send(json.dumps(result))
      await self.send(json.dumps(None))
      
    elif indict['code'] == 'setversion':
      self.myschoolline = await school.objects.aget(id=indict['school'])
      result = (self.myschoolline.model_xin, self.myschoolline.model_yin)
      await self.send(json.dumps(result))
      
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
          fitline = await fit.objects.filter(school = self.myschoolline.id).alatest('id')
          self.lastfit = fitline.id
          model_type = self.myschoolline.model_type
        except fit.DoesNotExist:
          self.lastfit = 0
          model_type = default_modeltype
        result = model_type
      elif indict['mode'] == 'sync':
        while True:
          try:
            fitline = await fit.objects.filter(school = self.myschoolline.id).alatest('id')
            fitline = fitline.id
          except fit.DoesNotExist:
            fitline = 0
          if fitline > self.lastfit:
            self.lastfit = fitline
            break
          else:
            await asyncio.sleep(1.0)
        mytoken = await maketoken_async('MOD', self.myschoolline.id, 'Download School #'+str(self.myschoolline.id))
        dlurl = settings.CLIENT_URL
        dlurl += 'trainers/downmodel/'
        dlurl += str(self.myschoolline.id) + '/' + str(mytoken[0]) + '/' + mytoken[1] +'/'
        result = dlurl
      elif indict['mode'] == 'check':
        fitline = await fit.objects.aget(id=self.lastfit)
        result = fitline.status =='Done' 
      logger.debug('--> ' + str(result))
      await self.send(json.dumps(result))	

  async def disconnect(self, code):
    logger.debug('Disconnected, Code:'+ str(code))

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
    self.ws_ts = None
    await self.accept()
    self.trainernr = None
    self.fit_list_done = 0
    self.one_more = False

  async def disconnect(self, code):
    if self.trainernr is not None:
      if self.didrunout:
        trainers[self.trainernr].stop_out(self.schoolnr)
      if self.trainerline.t_type in {2, 3}:
        self.ws.close()
        self.ws_session.close()
    logger.debug('Disconnected, Code:'+ str(code))

  async def receive(self, text_data):
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
        result = [] 
        if await all_fits.acount():
          returned = await all_fits.alast()
          self.working = (returned.status != 'Done')
          if (not self.working) and (not self.one_more):
            query_set= all_fits[self.fit_list_done:]
            added_one = False
          else:  
            if self.fit_list_done:
              query_set = all_fits[self.fit_list_done - 1:]
              added_one = True
            else:
              query_set = all_fits[self.fit_list_done:]
              added_one = False
            self.one_more = self.working
          self.fit_list_done = await all_fits.acount()
          async for item in query_set:
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
          added_one = False  
        outlist['data'] = (result, added_one)
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
          import aiohttp
          self.ws_session = aiohttp.ClientSession()
          self.ws = await self.ws_session.ws_connect(self.trainerline.wsserver + 'ws/trainerutil/')
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
      else:
        await self.close()
      if params['dorunout']:
        outlist['data'] = trainers[self.trainernr].run_out(self.schoolnr)
        self.didrunout = True
      else:
        outlist['data'] = 'OK'
        self.didrunout = False
      if outlist['data'] == 'Busy':
        self.trainernr = None
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

