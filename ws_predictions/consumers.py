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
import numpy as np
import cv2 as cv
from asyncio import sleep as asleep
from logging import getLogger
from traceback import format_exc
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from channels.generic.websocket import AsyncWebsocketConsumer
from globals.c_globals import tf_workers
from tools.c_logger import log_ini
from tools.l_tools import djconf
from access.c_access import access
from tf_workers.models import worker
from schools.c_schools import get_taglist

logname = 'ws_predictions'
logger = getLogger(logname)
log_ini(logger, logname)
taglist = get_taglist(1)
medium_brake = djconf.getconfigfloat('medium_brake', 0.1)
      
#*****************************************************************************
# predictionsConsumer
#*****************************************************************************

class predictionsConsumer(AsyncWebsocketConsumer):
  datacache = {}

  async def connect(self):
    try:
      self.authed = False
      self.permitted_schools = set()
      self.user = None
      self.ws_id = 0
      self.worker_nr = 0
      self.ws_name = 'undefined'
      self.mydatacache = {}
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (predictions)')
      logger.error(format_exc())

  async def disconnect(self, close_code):
    try:
      logger.info('Websocket-logout: WS-ID: ' + str(self.ws_id) 
        + ' - WS-Name: '  + str(self.ws_name) 
        + ' - Worker-Number: ' + str(self.worker_nr))
    except:
      logger.error('Error in consumer: ' + logname + ' (predictions)')
      logger.error(format_exc())

  async def checkschooldata(self, myschool):
    if not('schooldata' in self.mydatacache):
      self.mydatacache['schooldata'] = {}
    if myschool in self.mydatacache['schooldata']:
      if (('xdim' in self.mydatacache['schooldata'][myschool])
          and ('ydim' in self.mydatacache['schooldata'][myschool])):
        xytemp = (self.mydatacache['schooldata'][myschool]['xdim'],
          self.mydatacache['schooldata'][myschool]['ydim'])
        if 'tf_w_index' in self.mydatacache:
          return(xytemp)
    self.mydatacache['schooldata'][myschool] = {}
    tf_worker_object = await worker.objects.aget(school__id=myschool) 
    self.mydatacache['workernr'] = tf_worker_object.id
    self.mydatacache['tf_w_index'] = (
      tf_workers[self.mydatacache['workernr']].register())
    tf_workers[self.mydatacache['workernr']].run_out(
      self.mydatacache['tf_w_index'])
    xytemp = await tf_workers[self.mydatacache['workernr']].get_xy(
      myschool, self.mydatacache['tf_w_index'])
    self.mydatacache['schooldata'][myschool]['xdim'] = xytemp[0]
    self.mydatacache['schooldata'][myschool]['ydim'] = xytemp[1]
    return(xytemp)

  async def receive(self, text_data=None, bytes_data=None):
    try:
      if text_data:
        if text_data == 'Ping':
          logger.debug('Received Ping')
          return()
        intext = text_data
        #logger.info('<-- ' + str(intext))
        indict=json.loads(intext)
        if indict['code'] == 'auth':
          try:
            self.user = await User.objects.aget(username=indict['name'])
          except User.DoesNotExist:
            self.user = None  
            
          if self.user and await sync_to_async(
            self.user.check_password, 
            thread_sensitive=True, 
          )(indict['pass']):
            logger.debug('Success!')
            if not (indict['ws_id'] in self.datacache):
              self.datacache[indict['ws_id']] = {}
            if not (indict['worker_nr'] 
                in self.datacache[indict['ws_id']]):
              self.datacache[indict['ws_id']][indict['worker_nr']]=(
                {})
            self.mydatacache = (
              self.datacache[indict['ws_id']][indict['worker_nr']])
            if 'tf_w_index' in self.mydatacache:
              tf_workers[self.mydatacache['workernr']].stop_out(
                self.mydatacache['tf_w_index'])
              await tf_workers[self.mydatacache['workernr']].unregister(
                self.mydatacache['tf_w_index'])
              del self.mydatacache['tf_w_index']
            logger.info('Successful websocket-login: WS-ID: ' 
              + str(indict['ws_id']) 
              + ' - WS-Name: ' + str(indict['ws_name']) 
              + ' - Worker-Number: ' + str(indict['worker_nr']) 
              + ' - Software-Version: ' + indict['soft_ver'])
            self.ws_id = indict['ws_id']
            self.ws_name = indict['ws_name']
            self.worker_nr = indict['worker_nr']
            self.authed = True
            #logger.info('--> ' + 'OK')
            await self.send(json.dumps('OK'))
          else:
            logger.warning('Failure of websocket-login:  WS-ID: ' 
              + str(indict['ws_id']) 
              + ' - WS-Name: ' + str(indict['ws_name']) 
              + ' - Worker-Number: ' + str(indict['worker_nr']) 
              + ' - Software-Version: ' + indict['soft_ver'])
            await self.close() 
            return()
        elif indict['code'] == 'get_xy':
          myschool = indict['scho']
          xytemp = await self.checkschooldata(myschool)
          #logger.info('--> ' + str(xytemp))
          await self.send(json.dumps(xytemp))
        elif indict['code'] == 'imgl':
          if not('schooldata' in self.mydatacache):
            self.mydatacache['schooldata'] = {}
          if not self.authed:
            result = 'Unauthed user tried inferencing.'
            logger.error(result)
            await self.send(json.dumps(result))
            await self.close()
            return()
          myschool = indict['scho']
          if not (myschool in self.mydatacache['schooldata']):
            self.mydatacache['schooldata'][myschool] = {}
          if not (myschool in self.permitted_schools):
            if await access.check_async('S', myschool, self.user, 'R'):
              self.permitted_schools.add(myschool)
            else:
              result = 'User ' + str(self.user) + ' has no reading privilege for school #' + str(myschool)
              logger.error(result)
              await self.send(json.dumps(result))
              await self.close()
              return()
          try:
            self.mydatacache['schooldata'][myschool]['imglist'] = []
          except KeyError:
            logger.warning('KeyError while initializing ImgList')
          #logger.info('--> ' + 'OK')
          await self.send(json.dumps('OK'))
        elif indict['code'] == 'done':
          myschool = indict['scho'] 
          await self.checkschooldata(myschool)
          if ('imglist' in self.mydatacache['schooldata'][myschool]):
            if self.mydatacache['schooldata'][myschool]['imglist'] is not None:
              await tf_workers[self.mydatacache['workernr']].ask_pred(
                myschool, 
                self.mydatacache['schooldata'][myschool]['imglist'], 
                self.mydatacache['tf_w_index'],
              )
              my_worker = tf_workers[self.mydatacache['workernr']]
              predictions = np.empty((0, len(taglist)), np.float32)
              while (predictions.shape[0] 
                  < len(self.mydatacache['schooldata'][myschool]['imglist'])):
                while ('tf_w_index' not in self.mydatacache 
                    or my_worker.outqueue_empty(self.mydatacache['tf_w_index'])):
                  await asleep(medium_brake)
                predictions = np.vstack((predictions, 
                  await my_worker.get_from_outqueue(self.mydatacache['tf_w_index'])))
              predictions = predictions.tolist()
            else:
              logger.warning('Defective image in ws_predictions / consumers') 
              predictions = None        
          else:
            logger.warning('Incomplete image data in ws_predictions / consumers') 
            predictions = None   
          #logger.info('--> ' + str(predictions))
          await self.send(json.dumps(predictions))
        return()
      #bytes_data
      myschool = int.from_bytes(bytes_data[:8], 'big')
      if self.mydatacache['schooldata'][myschool]['imglist'] is not None:
        frame_ok = True
        try:
          logger.debug('<-- Length = ' + str(len(bytes_data)))
          frame = cv.imdecode(np.frombuffer(bytes_data, offset=8,
            dtype=np.uint8), cv.IMREAD_UNCHANGED)
          if len(frame.shape) != 3:
            frame_ok = False 
        except:
          frame_ok = False  
        if frame_ok:    
          try:
            if ((frame.shape[1] 
                  != self.mydatacache['schooldata'][myschool]['xdim'])
                or (frame.shape[0] 
                  != self.mydatacache['schooldata'][myschool]['ydim'])):
              frame = cv.resize(frame, (
                self.mydatacache['schooldata'][myschool]['ydim'], 
                self.mydatacache['schooldata'][myschool]['xdim']))
            frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)  
            self.mydatacache['schooldata'][myschool]['imglist'].append(frame)
          except KeyError:
            logger.warning('KeyError while adding image data')
        else:
          self.mydatacache['schooldata'][myschool]['imglist'] = None 
    except:
      logger.error('Error in consumer: ' + logname + ' (predictions)')
      logger.error(format_exc())
