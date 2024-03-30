# Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

import json
import cv2 as cv
import numpy as np
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
from tools.l_tools import djconf, seq_to_int, version_flat
from tools.c_logger import log_ini
from tools.djangodbasync import (getonelinedict, updatefilter, getoneline, 
  filterlinesdict, savedbline, deletefilter)
from access.c_access import access
from tools.tokens import maketoken
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

  @database_sync_to_async
  def checkfitdone(self, mode, schoolnr):
    if mode == 'init':
      try:    
        fitline = fit.objects.filter(school = schoolnr).latest('id')
        self.lastfit = fitline.id
        model_type = school.objects.get(id=schoolnr).model_type
      except fit.DoesNotExist:
        self.lastfit = 0
        model_type = default_modeltype
      return(model_type)
    elif mode == 'sync':
      while True:
        try:
          fitline = fit.objects.filter(school = schoolnr).latest('id').id
        except fit.DoesNotExist:
          fitline = 0
        if fitline > self.lastfit:
          self.lastfit = fitline
          break
        else:
          sleep(1.0)
      mytoken = maketoken('MOD', schoolnr, 'Download School #'+str(schoolnr))
      dlurl = settings.CLIENT_URL
      dlurl += 'trainers/downmodel/'
      dlurl += str(schoolnr) + '/' + str(mytoken[0]) + '/' + mytoken[1] +'/'
      return(dlurl)
    elif mode == 'check':
      fitline = fit.objects.get(id=self.lastfit)
      return(fitline.status =='Done')

  async def connect(self):
    self.frameinfo = {}
    self.client_soft_version = None
    await self.accept()

  async def receive(self, text_data =None, bytes_data=None):
    if bytes_data: 
      cod_x = self.myschooldict['model_xin']
      cod_y = self.myschooldict['model_yin']
      filepath = (self.myschooldict['dir'] 
        + 'coded/' + str(cod_x) + 'x' + str(cod_y) 
        + '/' + self.frameinfo['name'][:-4]+'.jpg')
      codpath = filepath[:-4]+'.cod'
      mydir = path.dirname(filepath) 
      if not path.exists(mydir):
        makedirs(mydir)
      imgdata = cv.imdecode(np.frombuffer(bytes_data, dtype=np.uint8), (cv.IMREAD_COLOR))
      if (imgdata.shape[1] != cod_x or  imgdata.shape[0] != cod_y):
        imgdata = cv.resize(imgdata, (cod_x, cod_y))
        cv.imwrite(filepath, imgdata)
        rename(filepath, codpath)
      else:
        with open(codpath, 'wb') as f:
          f.write(bytes_data)
      try:  
        frameline = await trainframe.objects.aget(
          name=self.frameinfo['name'], 
          school=self.myschooldict['id'],
        )
      except trainframe.DoesNotExist:  
        frameline = trainframe(
          made = timezone.make_aware(datetime.fromtimestamp(time())),
          school = self.myschooldict['id'],
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
      self.user = await getoneline(User, {'username' : indict['name'], })
      if self.user.check_password(indict['pass']):
        logger.debug('Success!')
        self.authed = True
      if not self.authed:
        logger.debug('Failure!')
        self.close() 
    elif indict['code'] == 'namecheck':
      try:
        sizeline = await img_size.objects.aget(x=self.myschooldict['model_xin'],
          y=self.myschooldict['model_yin'])
      except img_size.DoesNotExist:
        sizeline = img_size(x=self.myschooldict['model_xin'],
          y=self.myschooldict['model_yin'])
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
      self.myschooldict = await getonelinedict(school, 
        {'id' : indict['school'], }, 
        ['id', 'dir', 'model_xin', 'model_yin'], ) 
      self.client_soft_version = version_flat(indict['version'])
      result = (self.myschooldict['model_xin'], self.myschooldict['model_yin'])
      await self.send(json.dumps(result))
    elif indict['code'] == 'send':
      self.frameinfo['name'] = indict['name']
      self.frameinfo['tags'] = indict['tags']
      self.frameinfo['code'] = indict['framecode']
    elif indict['code'] == 'delete':
      await deletefilter(trainframe, {'name' : indict['name'], }, )
      bmppath = self.myschooldict['dir'] + 'frames/' + indict['name']
      if path.exists(bmppath):
        remove(bmppath)
      codpath = (self.myschooldict['dir'] 
        + 'coded/' 
        + str(self.myschooldict['model_xin']) 
        + 'x' + str(self.myschooldict['model_yin']) 
        + '/' + indict['name'][:-4]+'.cod')
      if path.exists(codpath):
        remove(codpath)
      await self.send('OK')
    elif indict['code'] == 'trainnow':
      await updatefilter(school, 
        {'id' : self.myschooldict['id'], }, 
        {'extra_runs' : 1, })
    elif indict['code'] == 'checkfitdone':
      result = await self.checkfitdone(indict['mode'], indict['school'])
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
      if self.dblinedict['t_type'] in {2, 3}:
        self.ws.close()
    logger.debug('Disconnected, Code:'+ str(code))

  @database_sync_to_async
  def getschoolinfo(self, schoolnr):
    countlist1 = trainframe.objects.filter(school=schoolnr)
    result = {}
    result['nr_total'] = countlist1.count()
    countlist = countlist1.filter(checked=True)
    result['nr_checked'] = countlist.count()
    result['nr_trained'] = countlist.filter(code='TR').count()
    result['nr_validated'] = countlist.filter(code='VA').count()
    result['nr_not_trained'] = countlist.filter(train_status__lt=2).count()
    result['nr_not_checked'] = result['nr_total'] - result['nr_checked']
    result['recog0'] = countlist1.filter(c0=1).count()
    result['recog1'] = countlist1.filter(c1=1).count()
    result['recog2'] = countlist1.filter(c2=1).count()
    result['recog3'] = countlist1.filter(c3=1).count()
    result['recog4'] = countlist1.filter(c4=1).count()
    result['recog5'] = countlist1.filter(c5=1).count()
    result['recog6'] = countlist1.filter(c6=1).count()
    result['recog7'] = countlist1.filter(c7=1).count()
    result['recog8'] = countlist1.filter(c8=1).count()
    result['recog9'] = countlist1.filter(c9=1).count()
    return(result)

  @database_sync_to_async
  def getfitinfo(self, schoolnr):
    all_fits = list(fit.objects.filter(school=schoolnr))
    if len(all_fits):
      self.working = (all_fits[-1].status != 'Done')
      if (not self.working) and (not self.one_more):
        result = all_fits[self.fit_list_done:]
        added_one = False
      else:  
        if self.fit_list_done:
          result = all_fits[self.fit_list_done - 1:]
          added_one = True
        else:
          result = all_fits[self.fit_list_done:]
          added_one = False
        self.one_more = self.working
      self.fit_list_done = len(all_fits)
    else:
      result = []  
      added_one = False
    result = serializers.serialize(
      'json', 
      result, 
      fields=(
        'made', 'nr_tr', 'nr_va', 'minutes', 'epochs', 'loss', 'cmetrics', 'val_loss', 
        'val_cmetrics', 'hit100', 'val_hit100', 'status', 'model_type', 
        'model_image_augmentation', 'model_weight_decay','model_weight_constraint', 
        'model_dropout', 'l_rate_start', 'l_rate_stop', 'l_rate_delta_min', 
        'l_rate_patience', 'l_rate_decrement', 'weight_min', 'weight_max', 
        'weight_boost', 'early_stop_delta_min', 'early_stop_patience', 
      ),
    )
    return((result, added_one))

  @database_sync_to_async
  def getepochsinfo(self, fitnr):
    result = serializers.serialize(
      'json', 
      list(epoch.objects.filter(fit=fitnr)), 
      fields=(
        'loss', 'cmetrics', 'val_loss', 'val_cmetrics', 
        'hit100', 'val_hit100', 'seconds', 'learning_rate',
      ),
    )
    return(result)

  async def receive(self, text_data):
    if text_data == 'Ping':
      return()
    logger.debug('<-- ' + text_data)
    params = json.loads(text_data)['data']	
    outlist = {'tracker' : json.loads(text_data)['tracker']}	

    if params['command'] == 'getschoolinfo':
      if self.dblinedict['t_type'] in {2, 3}:
        infolocal = await self.getschoolinfo(params['school'])
        temp = json.loads(text_data)
        temp['data']['school']=self.schoollinedict['e_school']
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        inforemote = json.loads(self.ws.recv())['data']
        infolocal['nr_trained'] = inforemote['nr_trained']
        infolocal['nr_validated'] = inforemote['nr_validated']
        outlist['data'] = infolocal
      else:
        outlist['data'] = await self.getschoolinfo(params['school'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))				

    elif params['command'] == 'getfitinfo':
      if self.dblinedict['t_type'] in {2, 3}:
        temp = json.loads(text_data)
        temp['data']['school']=self.schoollinedict['e_school']
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        outlist['data'] = await self.getfitinfo(params['school'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))					

    elif params['command'] == 'checkfitdone':
      if self.dblinedict['t_type'] in {2, 3}:
        self.ws.send(text_data, opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        outlist['data'] = await self.checkfitdone(params['fitnr'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))						

    elif params['command'] == 'getepochsinfo':
      if self.dblinedict['t_type'] in {2, 3}:
        temp = json.loads(text_data)
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        outlist['data'] = await self.getepochsinfo(params['fitnr'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))								

    elif params['command'] == 'getparams':
      if self.dblinedict['t_type'] in {2, 3}:
        self.ws.send(text_data, opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        paramline = await getonelinedict(fit, 
          {'id' : params['fitnr'], }, 
          ['model_type', 'model_image_augmentation', 'model_weight_decay', 
            'model_weight_constraint', 'model_dropout', 'l_rate_start', 
            'l_rate_stop', 'l_rate_delta_min', 'l_rate_patience', 
            'l_rate_decrement', 'weight_min', 'weight_max', 
            'weight_boost', 'early_stop_delta_min', 'early_stop_patience', 
          ])
        outlist['data'] = paramline
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))							

    elif params['command'] == 'connecttrainer':
      self.schoolnr = params['school']
      if self.scope['user'].is_authenticated:
        myuser = self.scope['user']
      else:
        myuser = await getoneline(User, {'username' : params['name'], })
        if myuser.check_password(params['pass']):
          self.authed = True
        if not self.authed:
          self.close() 
      if access.check('S', self.schoolnr, myuser, 'R'):
        self.maywrite = access.check('S', self.schoolnr, myuser, 'W')
        self.schoollinedict = await getonelinedict(school, 
          {'id' : self.schoolnr, }, 
          ['dir', 'trainer', 'tf_worker', 'e_school', ])
        self.trainernr = self.schoollinedict['trainer']
        tf_workerlinedict = await getonelinedict(worker, 
          {'id' : self.schoollinedict['tf_worker'], }, 
          ['wsname', 'wspass', ])
        self.dblinedict = await getonelinedict(dbtrainer, 
          {'id' : self.trainernr, }, 
          ['t_type', 'wsserver', ], )
        if self.dblinedict['t_type'] in {2, 3}:
          from websocket import WebSocket #, enableTrace
          #enableTrace(True)
          self.ws_ts = time()
          self.ws = WebSocket()
          self.ws.connect(self.dblinedict['wsserver'] + 'ws/trainerutil/')
          temp = json.loads(text_data)
          temp['data']['school']=self.schoollinedict['e_school']
          temp['data']['name']=tf_workerlinedict['wsname']
          temp['data']['pass']=tf_workerlinedict['wspass']
          temp['data']['dorunout']=params['dorunout']
          self.ws.send(json.dumps(temp), opcode=1) #1 = Text
          if json.loads(self.ws.recv())['data'] != 'OK':
            self.close()	
      else:
        self.close()
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
      if self.dblinedict['t_type'] in {2, 3}:
        temp = json.loads(text_data)
        temp['data']['school']=self.schoollinedict['e_school']
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
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
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'extra_runs' : 1, })
        outlist['data'] = 'OK' 
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
      else:
        self.close()		
        
    elif params['command'] == 'get_for_dashboard':  	
      if self.dblinedict['t_type'] in {2, 3}:
        temp = json.loads(text_data)
        temp['data']['school']=self.schoollinedict['e_school']
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        answer = json.loads(self.ws.recv())['data']
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {params['item'] : answer, }) 
        outlist['data'] = answer
      else:  
        schooldict = await getonelinedict(school, 
          {'id' : self.schoolnr, }, 
          [params['item']]) 
        outlist['data'] = schooldict[params['item']]
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))						

    elif params['command'] == 'set_from_dashboard':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {params['item'] : params['value'], }) 
        if self.dblinedict['t_type'] in {2, 3}:
          temp = json.loads(text_data)
          temp['data']['school']=self.schoollinedict['e_school']
          self.ws.send(json.dumps(temp), opcode=1) #1 = Text
          if json.loads(self.ws.recv())['data'] != 'OK':
            self.close()	
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
      else:
        self.close()						

    elif params['command'] == 'getavailmodels':
      if self.dblinedict['t_type'] == 3:
        temp = json.loads(text_data)
        temp['data']['school']=self.schoollinedict['e_school']
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        modeldir = self.schoollinedict['dir']
        outlist['data'] = []
        model_type_dict = await filterlinesdict(model_type, fields=['name', ])
        for item in  model_type_dict:
          search_path = modeldir + 'model/' + item['name']
          if path.exists(search_path + '.h5'):
            outlist['data'].append(item['name'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))			

