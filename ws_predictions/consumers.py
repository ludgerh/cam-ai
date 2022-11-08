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
from traceback import format_exc
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
  datacache = {}

  def connect(self):
    self.accept()
    self.authed = False
    self.permitted_schools = set()
    self.user = None
    self.server_nr = 0
    self.worker_nr = 0

  def disconnect(self, close_code):
    logger.info('Websocket-logout: System-Nr.: ' + str(self.server_nr) 
      + ' - Worker-Number: ' + str(self.worker_nr))

  def checkschooldata(self, myschool):
    if not('schooldata' in self.mydatacache):
      self.mydatacache['schooldata'] = {}
    if not (myschool in self.mydatacache['schooldata']):
      self.mydatacache['schooldata'][myschool] = {}
      self.mydatacache['workernr'] = school.objects.get(id=myschool).tf_worker.id
      self.mydatacache['tf_w_index'] = tf_workers[self.mydatacache['workernr']].register()
      tf_workers[self.mydatacache['workernr']].run_out(self.mydatacache['tf_w_index'])
      xytemp = tf_workers[self.mydatacache['workernr']].get_xy(
        myschool, self.mydatacache['tf_w_index'])
      self.mydatacache['schooldata'][myschool]['xdim'] = xytemp[0]
      self.mydatacache['schooldata'][myschool]['ydim'] = xytemp[1]
    else:
      xytemp = (self.mydatacache['schooldata'][myschool]['xdim'],
        self.mydatacache['schooldata'][myschool]['ydim'])
    return(xytemp)

  def receive(self, text_data=None, bytes_data=None):
    try:
      if text_data:
        if text_data == 'Ping':
          logger.debug('Received Ping')
        else:
          intext = text_data
          logger.debug('<-- ' + str(intext))
          indict=json.loads(intext)
          if indict['code'] == 'auth':
            self.user = User.objects.get(username=indict['name'])
            if self.user.check_password(indict['pass']):
              logger.debug('Success!')
              if not (indict['server_nr'] in self.datacache):
                self.datacache[indict['server_nr']] = {}
              if not (indict['worker_nr'] 
                  in self.datacache[indict['server_nr']]):
                self.datacache[indict['server_nr']][indict['worker_nr']]=(
                  {})
              self.mydatacache = (
                self.datacache[indict['server_nr']][indict['worker_nr']])
              if 'tf_w_index' in self.mydatacache:
                tf_workers[self.mydatacache['workernr']].stop_out(self.mydatacache['tf_w_index'])
                tf_workers[self.mydatacache['workernr']].unregister(self.mydatacache['tf_w_index'])
                del self.mydatacache['tf_w_index']
              logger.info('Successful websocket-login: System-Nr.: ' 
                + str(indict['server_nr'])  + ' - Worker-Number: ' + str(indict['worker_nr']))
              self.server_nr = indict['server_nr']
              self.worker_nr = indict['worker_nr']
              self.authed = True
            else:
              logger.warning('Failure of websocket-login: ' 
                + str(indict['server_nr']) + '-' + str(indict['worker_nr']))
              self.close() 
          elif indict['code'] == 'get_xy':
            myschool = indict['scho']
            xytemp = self.checkschooldata(myschool)
            logger.debug('--> ' + str(xytemp))
            self.send(json.dumps(xytemp))
          elif indict['code'] == 'imgl':
            if not('schooldata' in self.mydatacache):
              self.mydatacache['schooldata'] = {}
            if not self.authed:
              self.close()
            myschool = indict['scho']
            if not (myschool in self.mydatacache['schooldata']):
              self.mydatacache['schooldata'][myschool] = {}
            if not (myschool in self.permitted_schools):
              if access.check('S', myschool, self.user, 'R'):
                self.permitted_schools.add(myschool)
              else:
                self.close()
            self.mydatacache['schooldata'][myschool]['numberofframes'] = indict['nrf']
            self.mydatacache['schooldata'][myschool]['imglist'] = np.empty((
              0, self.mydatacache['schooldata'][myschool]['xdim'], 
              self.mydatacache['schooldata'][myschool]['ydim'], 3), np.uint8)
          elif indict['code'] == 'done':
            myschool = indict['scho']
            self.checkschooldata(myschool)
            if ('imglist' in self.mydatacache['schooldata'][myschool]):
              tf_workers[self.mydatacache['workernr']].client_check_model(myschool, test_pred = False)
              tf_workers[self.mydatacache['workernr']].ask_pred(
                myschool, 
                self.mydatacache['schooldata'][myschool]['imglist'], 
                self.mydatacache['tf_w_index'],
                [],
                -1,
              )
              predictions = np.empty((0, len(taglist)), np.float32)
              while predictions.shape[0]<self.mydatacache['schooldata'][myschool]['imglist'].shape[0]:
                predictions = np.vstack((predictions, 
                  tf_workers[self.mydatacache['workernr']].get_from_outqueue(
                    self.mydatacache['tf_w_index'])))
              logger.debug('--> ' + str(predictions))
              self.send(json.dumps(predictions.tolist()))
            else:
              self.send('incomplete')
      else: #bytes_data
        myschool = int.from_bytes(bytes_data[:8], 'big')
        logger.debug('<-- Length = ' + str(len(bytes_data)))
        frame = cv.imdecode(np.frombuffer(bytes_data, offset=8,
          dtype=np.uint8), cv.IMREAD_UNCHANGED)
        frame = np.expand_dims(frame, axis=0)
        self.mydatacache['schooldata'][myschool]['imglist'] = np.vstack((
          self.mydatacache['schooldata'][myschool]['imglist'], frame))
        self.mydatacache['schooldata'][myschool]['numberofframes'] -= 1
    except:
      logger.error(format_exc())
      logger.handlers.clear()
