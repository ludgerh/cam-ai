# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
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
from os import remove
from time import time
from datetime import datetime
from logging import getLogger
from traceback import format_exc
from django.core import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tools.l_tools import djconf, seq_to_int
from tools.c_logger import log_ini
from tools.djangodbasync import (getonelinedict, updatefilter, getoneline, 
  filterlinesdict, savedbline, deletefilter)
from access.c_access import access
from tf_workers.models import school, worker
from .models import trainframe, fit, epoch, trainer as dbtrainer
from .c_trainers import trainers

logname = 'ws_trainerconsumers'
logger = getLogger(logname)
log_ini(logger, logname)

#*****************************************************************************
# RemoteTrainer
#*****************************************************************************

class remotetrainer(AsyncWebsocketConsumer):

  async def connect(self):
    self.frameinfo = {}
    await self.accept()

  async def receive(self, text_data =None, bytes_data=None):
    try:
      if bytes_data:
        filepath = self.myschooldict['dir'] + self.frameinfo['name']
        with open(filepath, 'wb') as f:
          f.write(bytes_data)
        frameline = trainframe(
          made = timezone.make_aware(datetime.fromtimestamp(time())),
          school = self.myschooldict['id'],
          name = self.frameinfo['name'],
          code = 'NE',
          c0 = self.frameinfo['tags'][0], c1 = self.frameinfo['tags'][1],
          c2 = self.frameinfo['tags'][2], c3 = self.frameinfo['tags'][3],
          c4 = self.frameinfo['tags'][4], c5 = self.frameinfo['tags'][5],
          c6 = self.frameinfo['tags'][6], c7 = self.frameinfo['tags'][7],
          c8 = self.frameinfo['tags'][8], c9 = self.frameinfo['tags'][9],
          checked = 1,
          train_status = 1,
        )
        await savedbline(frameline)
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
        self.myschooldict = await getonelinedict(school, 
          {'id' : indict['school'], }, 
          ['id', 'dir',], )
        myframes = await filterlinesdict(trainframe, 
          {'school' : indict['school'], }, 
          ['name', 'c0', 'c1', 'c2', 'c3', 'c4', 'c5', 'c6', 'c7', 
            'c8', 'c9',], )
        result = [(item['name'], seq_to_int((item['c0'], item['c1'], 
            item['c2'], item['c3'], item['c4'], item['c5'], item['c6'], 
            item['c7'], item['c8'], item['c9'])))
          for item in myframes]
        await self.send(json.dumps(result))
      elif indict['code'] == 'send':
        self.frameinfo['name'] = indict['name']
        self.frameinfo['tags'] = indict['tags']
      elif indict['code'] == 'delete':
        await deletefilter(trainframe, {'name' : indict['name'], }, )
        remove(self.myschooldict['dir'] + indict['name'])
      elif indict['code'] == 'trainnow':
        await updatefilter(school, 
          {'id' : self.myschooldict['id'], }, 
          {'extra_runs' : 1, })
    except:
      logger.error(format_exc())
      logger.handlers.clear()

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
          sleep(djconf.getconfigfloat('medium_brake', 0.1))

  async def connect(self):
    self.ws_ts = None
    await self.accept()
    self.trainernr = None

  async def disconnect(self, code):
    if self.trainernr is not None:
      if self.didrunout:
        trainers[self.trainernr].stop_out(self.schoolnr)
      if self.dblinedict['t_type'] == 3:
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
    result = serializers.serialize(
      'json', 
      list(fit.objects.filter(school=schoolnr)), 
      fields=(
        'made', 'nr_tr', 'nr_va', 'minutes', 
        'epochs', 'loss', 'cmetrics', 'val_loss', 
        'val_cmetrics', 'cputemp', 'cpufan1', 'cpufan2',
        'gputemp','gpufan', 'hit100', 'val_hit100',
        'status',
      ),
    )
    return(result)

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
      if self.dblinedict['t_type'] == 3:
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
      if self.dblinedict['t_type'] == 3:
        temp = json.loads(text_data)
        temp['data']['school']=self.schoollinedict['e_school']
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        outlist['data'] = await self.getfitinfo(params['school'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))						

    elif params['command'] == 'getepochsinfo':
      if self.dblinedict['t_type'] == 3:
        temp = json.loads(text_data)
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        outlist['data'] = await self.getepochsinfo(params['fitnr'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))								

    elif params['command'] == 'getparams':
      if self.dblinedict['t_type'] == 3:
        temp = json.loads(text_data)
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
      else:
        paramline = await getonelinedict(fit, 
          {'id' : params['fitnr'], }, 
          ['description', ])
        paramline = paramline['description']
        paramline = '<br>'.join(paramline.splitlines())
        #paramline = paramline.replace('<br><br>', '<br>')
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
          logger.debug('Success!')
          self.authed = True
        if not self.authed:
          logger.debug('Failure!')
          self.close() 
      if access.check('S', self.schoolnr, myuser, 'R'):
        self.maywrite = access.check('S', self.schoolnr, myuser, 'W')
        self.schoollinedict = await getonelinedict(school, 
          {'id' : self.schoolnr, }, 
          ['trainer', 'tf_worker', 'e_school', ])
        self.trainernr = self.schoollinedict['trainer']
        tf_workerlinedict = await getonelinedict(worker, 
          {'id' : self.schoollinedict['tf_worker'], }, 
          ['wsname', 'wspass', ])
        self.dblinedict = await getonelinedict(dbtrainer, 
          {'id' : self.trainernr, }, 
          ['t_type', 'wsserver', ], )
        if self.dblinedict['t_type'] == 3:
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
      if self.dblinedict['t_type'] == 3:
        temp = json.loads(text_data)
        temp['data']['school']=self.schoollinedict['e_school']
        self.ws.send(json.dumps(temp), opcode=1) #1 = Text
        outlist['data'] = json.loads(self.ws.recv())['data']
        #await self.send_ping()  
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

    elif params['command'] == 'gettrigger':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['trigger']) 
      outlist['data'] = schooldict['trigger']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))				

    elif params['command'] == 'getpatience':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['patience']) 
      outlist['data'] = schooldict['patience']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))					

    elif params['command'] == 'getmaxweight':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['weight_max']) 
      outlist['data'] = schooldict['weight_max']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))					

    elif params['command'] == 'getminweight':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['weight_min']) 
      outlist['data'] = schooldict['weight_min']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))					

    elif params['command'] == 'getweightboost':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['weight_boost']) 
      outlist['data'] = schooldict['weight_boost']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))				

    elif params['command'] == 'getminlr':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['l_rate_min']) 
      outlist['data'] = schooldict['l_rate_min']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))					

    elif params['command'] == 'getmaxlr':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['l_rate_max']) 
      outlist['data'] = schooldict['l_rate_max']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))						

    elif params['command'] == 'getignorecheck':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['ignore_checked']) 
      outlist['data'] = schooldict['ignore_checked']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))								

    elif params['command'] == 'getdonate':
      schooldict = await getonelinedict(school, 
        {'id' : self.schoolnr, }, 
        ['donate_pics']) 
      outlist['data'] = schooldict['donate_pics']
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))					

    elif params['command'] == 'settrigger':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'trigger' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setpatience':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'patience' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setmaxweight':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'weight_max' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setminweight':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'weight_min' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setweightboost':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'weight_boost' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setminlr':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'l_rate_min' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setmaxlr':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'l_rate_max' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setignorecheck':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'ignore_checked' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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

    elif params['command'] == 'setdonate':
      if self.maywrite:
        await updatefilter(school, 
          {'id' : self.schoolnr, }, 
          {'donate_pics' : params['value'], }) 
        if self.dblinedict['t_type'] == 3:
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
