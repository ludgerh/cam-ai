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
import numpy as np
import cv2 as cv
from logging import getLogger
from time import sleep
from django.contrib.auth.models import User
from channels.generic.websocket import WebsocketConsumer
from tools.c_logger import log_ini
from tools.l_tools import djconf
from access.c_access import access
from tf_workers.c_tfworkers import tf_workers
from tf_workers.models import school
from schools.c_schools import get_taglist

logname = 'ws_predictionsconsumers'
logger = getLogger(logname)
log_ini(logger, logname)
taglist = get_taglist(1)
      
#*****************************************************************************
# predictionsConsumer
#*****************************************************************************

class predictionsConsumer(WebsocketConsumer):

  def connect(self):
    self.accept()
    self.authed = False
    self.permitted_schools = set()
    self.user = None
    self.numberofframes = 0
    self.schooldatacache = {}
    self.eventdict = {}

  def receive(self, text_data=None, bytes_data=None):
    if bytes_data:
      myitem = self.schooldatacache[self.school]
      logger.debug('<-- Length = ' + str(len(bytes_data)))
      frame = cv.imdecode(np.frombuffer(bytes_data, dtype=np.uint8), cv.IMREAD_UNCHANGED)
      frame = np.expand_dims(frame, axis=0)
      self.imglist = np.vstack((self.imglist, frame))
      self.numberofframes -= 1
      if self.numberofframes == 0:
        tf_workers[myitem['workernr']].ask_pred(
          self.school, 
          self.imglist, 
          myitem['tf_w_index'],
          [],
          -1,
        )
        predictions = np.empty((0, len(taglist)), np.float32)
        while predictions.shape[0] < self.imglist.shape[0]:
          predictions = np.vstack((predictions, tf_workers[myitem['workernr']].get_from_outqueue(myitem['tf_w_index'])))
        logger.debug('--> ' + str(predictions))
        self.send(json.dumps(predictions.tolist()))
      return()
    if text_data == 'Ping':
      logger.debug('Received Ping')
      return()
    intext = text_data
    logger.debug('<-- ' + str(intext))
    indict=json.loads(intext)
    if indict['code'] == 'imgl':
      if not self.authed:
        self.close()
      if not (indict['scho'] in self.permitted_schools):
        if access.check('S', indict['scho'], self.user, 'R'):
          self.permitted_schools.add(indict['scho'])
        else:
          self.close()
      self.numberofframes = indict['nrf']
      self.school = indict['scho']
      while not(self.school in self.schooldatacache):
        logger.warning('Schooldatacache not ready')
        sleep(djconf.getconfigfloat('long_brake', 1.0))
      self.imglist = np.empty((
        0, self.schooldatacache[self.school]['xdim'], 
        self.schooldatacache[self.school]['ydim'], 3), np.uint8)
    elif indict['code'] == 'auth':
      self.user = User.objects.get(username=indict['name'])
      if self.user.check_password(indict['pass']):
        logger.debug('Success!')
        self.authed = True
      if not self.authed:
        logger.info('Failure!')
        self.close() 
    elif indict['code'] == 'get_xy':
      myschool = indict['scho']
      if myschool in self.schooldatacache:
        myitem = self.schooldatacache[myschool]
      else:
        myitem = {}
        myitem['workernr'] = school.objects.get(id=myschool).tf_worker.id
        myitem['tf_w_index'] = tf_workers[myitem['workernr']].register()
        tf_workers[myitem['workernr']].run_out(myitem['tf_w_index'])
        xytemp = tf_workers[myitem['workernr']].get_xy(
          myschool, myitem['tf_w_index'])
        myitem['xdim'] = xytemp[0]
        myitem['ydim'] = xytemp[1]
        self.schooldatacache[myschool] = myitem
      outtuple = (myitem['xdim'], myitem['ydim'])
      logger.debug('--> ' + str(outtuple))
      self.send(json.dumps(outtuple))

  def disconnect(self, close_code):
    for item in self.schooldatacache.values():
      tf_workers[item['workernr']].unregister(item['tf_w_index'])


