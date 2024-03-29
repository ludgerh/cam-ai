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
import numpy as np
import cv2 as cv
from time import time, sleep
from logging import getLogger
from traceback import format_exc
from zlib import compress
from threading import Event
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
from autobahn.exception import Disconnected
from access.c_access import access
from streams.startup import streams
from tools.c_redis import myredis
from tools.c_logger import log_ini
from tools.c_tools import c_convert
from tools.l_tools import djconf
from tools.tokens import checktoken
from tools.djangodbasync import savedbline, updatefilter
from .models import view_log

logname = 'ws_viewconsumers'
logger = getLogger(logname)
log_ini(logger, logname)

redis = myredis()

longbreak = djconf.getconfigfloat('long_brake', 1.0)
is_public_server = djconf.getconfigbool('is_public_server', False)

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
    self.outxdict = {}
    self.busydict = {}
    self.accept()

  def disconnect(self, close_code):
    for viewer in self.viewerlist:
      viewer.parent.take_view_count()
      if not redis.view_from_dev(viewer.parent.type, viewer.parent.id):
        if self.indexdict[viewer.parent.type][viewer.parent.id]['show_cam']:
          viewer.pop_from_onf(self.indexdict[viewer.parent.type][viewer.parent.id]['onf'])
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
      self.busydict[text_data].clear()
      return()
    params = json.loads(text_data)['data']
    try:
      outlist = {'tracker' : json.loads(text_data)['tracker']}

      if params['command'] == 'starttrigger':
        mystream = streams[params['idx']]
        show_cam = not(self.scope['user'].is_superuser 
          and is_public_server and mystream.dbline.encrypted)
        if access.check(params['mode'], params['idx'], self.scope['user'], 'R'):
          outx = params['width']
          if params['mode'] == 'C':
            if outx > mystream.dbline.cam_min_x_view:
              outx *= mystream.dbline.cam_scale_x_view
              outx = max(mystream.dbline.cam_min_x_view, outx)
              if mystream.dbline.cam_max_x_view:
                outx = min(mystream.dbline.cam_max_x_view, outx)
            myviewer = mystream.mycam.viewer
          elif params['mode'] == 'D':
            mydetector = mystream.mydetector
            while mydetector.scaledown is None:
              sleep(longbreak)
            if outx > mystream.dbline.det_min_x_view:
              outx *= mystream.dbline.det_scale_x_view
              outx = max(mystream.dbline.det_min_x_view, outx)
              if mystream.dbline.det_max_x_view:
                outx = min(mystream.dbline.det_max_x_view, outx)
              if mydetector.scaledown > 1:
                outx = min(outx, mystream.dbline.cam_xres / mydetector.scaledown)
            myviewer = mydetector.viewer
          elif params['mode'] == 'E':
            myeventer = mystream.myeventer
            myeventer.inqueue.put(('setdscrwidth', outx, ))
            if outx > mystream.dbline.eve_min_x_view:
              outx *= mystream.dbline.eve_scale_x_view
              outx = max(mystream.dbline.eve_min_x_view, outx)
              if mystream.dbline.eve_max_x_view:
                outx = min(mystream.dbline.eve_max_x_view, outx)
            myviewer = myeventer.viewer
          outx = min(mystream.dbline.cam_xres, outx)
          self.outxdict[params['idx']] = round(outx)
          self.queuedict[params['idx']] = myviewer.inqueue
          busy_idx = params['mode']+str(params['idx']).zfill(9)
          self.busydict[busy_idx] = Event()
          self.busydict[busy_idx].set()
          if show_cam:
          
            def onf(onf_viewer):  
              try:
                indicator = onf_viewer.parent.type+str(onf_viewer.parent.id).zfill(9)
                if not self.busydict[indicator].is_set():
                  self.busydict[indicator].set()
                  ts = time()
                  frame = onf_viewer.inqueue.get()[1]
                  if params['mode'] == 'D':
                    if (onf_viewer.drawpad.show_mask 
                        and (onf_viewer.drawpad.mask is not None)):
                      frame = cv.addWeighted(frame, 1, 
                        (255-onf_viewer.drawpad.mask), 0.3, 0)
                  elif params['mode'] == 'C':
                    if (onf_viewer.drawpad.show_mask 
                        and (onf_viewer.drawpad.mask is not None)):
                      frame = cv.addWeighted(frame, 1, 
                        (255-onf_viewer.drawpad.mask), -0.3, 0)
                    if onf_viewer.drawpad.edit_active and onf_viewer.drawpad.ringlist:
                      if onf_viewer.drawpad.whitemarks:
                        frame = cv.addWeighted(frame, 1, 
                          (255-onf_viewer.drawpad.screen), 1, 0)
                      else:
                        frame = cv.addWeighted(frame, 1, 
                          (255-onf_viewer.drawpad.screen), -1.0, 0)
                  frame = c_convert(frame, typein=1, typeout=3, 
                    xout=self.outxdict[onf_viewer.parent.id])
                  if (int(redis.get('CAM-AI:KBInt')) 
                      or int(redis.get('CAM-AI:KillStream:'+str(params['idx'])))):
                    return()  
                  try:
                    self.send(bytes_data=indicator.encode()+frame)
                  except Disconnected:
                    logger.warning('*** Could not send Frame, socket closed...')
              except:
                logger.error(format_exc())
                logger.handlers.clear()

          myviewer.parent.add_view_count()
          if params['mode'] not in self.indexdict:
            self.indexdict[params['mode']] = {}
          self.indexdict[params['mode']][params['idx']] = {'show_cam' : show_cam, }
          if show_cam:
            self.indexdict[params['mode']][params['idx']]['onf'] = myviewer.push_to_onf(
              onf, )
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
          outlist['data'] = {
            'outx' : self.outxdict[params['idx']], 
            'show_cam' : show_cam,
          }
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

  @database_sync_to_async
  def mychecktoken(self, *args):
    return(checktoken(*args))

  async def connect(self):
    await self.accept()

  async def receive(self, text_data):
    logger.debug('<-- ' + str(text_data))
    params = json.loads(text_data)['data']
    outlist = {'tracker' : json.loads(text_data)['tracker']}

    if params['command'] == 'getcaminfo':
      go_on = access.check(params['mode'], params['idx'], self.scope['user'], 'R')
      if go_on:
        outlist['data'] = {}
        outlist['data']['fps'] = round(redis.fps_from_dev(params['mode'], 
          params['idx']), 2)
        outlist['data']['viewers'] = redis.view_from_dev(params['mode'], params['idx'])
        logger.debug('--> ' + str(outlist))
        try:
          await self.send(json.dumps(outlist))	
        except Disconnected:
          logger.warning('*** Could not send Cam Info , socket closed...')
      else:
        await self.close()
