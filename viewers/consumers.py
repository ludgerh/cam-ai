import json
import cv2 as cv
from time import time, sleep
from logging import getLogger
from traceback import format_exc
import numpy as np
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from autobahn.exception import Disconnected
from access.c_access import access
from streams.startup import streams
from tools.c_redis import myredis
from tools.c_logger import log_ini
from tools.c_tools import c_convert
from tools.l_tools import djconf
from tools.djangodbasync import savedbline, updatefilter
from .models import view_log

logname = 'ws_viewconsumers'
logger = getLogger(logname)
log_ini(logger, logname)

redis = myredis()

#*****************************************************************************
# triggerConsumer
# This is not async because the funtion ONF gets called from Sync
#*****************************************************************************

class triggerConsumer(WebsocketConsumer):

  def connect(self):
    self.viewerlist = []
    self.indexdict = {}
    self.loglist = []
    self.queuedict = {}
    self.dimdict = {}
    self.busydict = {}
    self.accept()

  def disconnect(self, close_code):
    for viewer in self.viewerlist:
      viewer.parent.take_view_count()
      if not redis.view_from_dev(viewer.parent.type, viewer.parent.id):
        viewer.inqueue.stop()
        viewer.pop_from_onf(self.indexdict[viewer.parent.id])
    for item in self.loglist:
      item.stop = timezone.now()
      item.active = False
      while True:
        try:
          item.save(update_fields=["stop", "active", ])
          break
        except OperationalError:
          connection.close()

  def receive(self, text_data):
    logger.debug('<-- ' + str(text_data))
    if text_data[0] in {'C', 'D', 'E'}:
      self.busydict[text_data] = False
      return()
    params = json.loads(text_data)['data']
    try:
      outlist = {'tracker' : json.loads(text_data)['tracker']}

      if params['command'] == 'starttrigger':
        if access.check(params['mode'], params['idx'], self.scope['user'], 'R'):
          if params['mode'] == 'C':
            myviewer = streams[params['idx']].mycam.viewer
          elif params['mode'] == 'D':
            myviewer = streams[params['idx']].mydetector.viewer
          elif params['mode'] == 'E':
            myviewer = streams[params['idx']].myeventer.viewer
          self.queuedict[params['idx']] = myviewer.inqueue
          self.dimdict[params['idx']] = (params['width'], params['height'])
          self.busydict[params['mode']+str(params['idx']).zfill(9)] = False
          def onf(onf_viewer):
            indicator = onf_viewer.parent.type+str(onf_viewer.parent.id).zfill(9)
            if not self.busydict[indicator]:
              self.busydict[indicator] = True
              #ts = time()
              frame = onf_viewer.inqueue.get()[1]
              if params['mode'] == 'D':
                if onf_viewer.drawpad.show_mask and (onf_viewer.drawpad.mask is not None):
                  frame = cv.addWeighted(frame, 1, (255-onf_viewer.drawpad.mask), 0.3, 0)
              elif params['mode'] == 'C':
                if onf_viewer.drawpad.show_mask and (onf_viewer.drawpad.mask is not None):
                  frame = cv.addWeighted(frame, 1, (255-onf_viewer.drawpad.mask), -0.3, 0)
              if params['mode'] in {'C', 'D'}:
                if onf_viewer.drawpad.edit_active and onf_viewer.drawpad.ringlist:
                  if onf_viewer.drawpad.whitemarks:
                    frame = cv.addWeighted(frame, 1, (255-onf_viewer.drawpad.screen), 1, 0)
                  else:
                    frame = cv.addWeighted(frame, 1, (255-onf_viewer.drawpad.screen), -1.0, 0)
              dimtemp = self.dimdict[onf_viewer.parent.id]
              frame = c_convert(frame, typein=3, xout=dimtemp[0], yout=dimtemp[1])
              frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
              dims3 = (dimtemp[1], dimtemp[0], 1)
              alpha = np.full(dims3, 255, dtype=np.uint8)
              frame = np.concatenate((frame, alpha), axis=2)
              #print('*** Preparation:', time() - ts)
              #ts = time()
              try:
                self.send(bytes_data=indicator.encode()+frame.tobytes()) 
              except Disconnected:
                logger.error('*** Could not send Trigger, socket closed...')
              #print('*** Sending:', time() - ts)
          myviewer.parent.add_view_count()
          self.indexdict[params['idx']] = myviewer.push_to_onf(onf)
          myviewer.inqueue.register_callback()
          self.viewerlist.append(myviewer)
          if self.scope['user'].is_authenticated:
            myuser = self.scope['user'].id
          else:
            myuser = -1
          my_log_line = view_log(v_type=params['mode'],
            v_id=params['idx'],
            start=timezone.now(),
            stop=timezone.now(),
            user=myuser,
            active=True,
          )
          my_log_line.save()
          self.loglist.append(my_log_line)
          outlist['data'] = 'OK'
          outlist = ('C', outlist)
          logger.debug('--> ' + str(outlist))
          self.send(json.dumps(outlist))
        else:
          self.close()
    except:
      logger.error(format_exc())
      logger.handlers.clear()

#*****************************************************************************
# c_viewConsumer
#*****************************************************************************

class c_viewConsumer(AsyncWebsocketConsumer):

  async def connect(self):
    await self.accept()

  async def receive(self, text_data):
    logger.debug('<-- ' + str(text_data))
    params = json.loads(text_data)['data']
    outlist = {'tracker' : json.loads(text_data)['tracker']}

    if params['command'] == 'getcaminfo':
      if access.check(params['mode'], params['idx'], self.scope['user'], 'R'):
        outlist['data'] = {}
        outlist['data']['fps'] = round(redis.fps_from_dev(params['mode'], params['idx']), 2)
        outlist['data']['viewers'] = redis.view_from_dev(params['mode'], params['idx'])
        logger.debug('--> ' + str(outlist))
        try:
          await self.send(json.dumps(outlist))	
        except Disconnected:
          print('*** Could not send Cam Info , socket closed...')
      else:
        await self.close()
