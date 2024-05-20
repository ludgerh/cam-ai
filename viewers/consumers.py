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
import asyncio
from time import sleep
from logging import getLogger
from django.utils import timezone
from django.db import connection
from django.db.utils import OperationalError
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from autobahn.exception import Disconnected
from access.c_access import access
from asgiref.sync import sync_to_async
from streams.startup import streams
from tools.c_redis import myredis
from tools.c_logger import log_ini
from tools.l_tools import djconf
from tools.tokens import checktoken
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

class triggerConsumer(AsyncWebsocketConsumer):

  async def connect(self):
    self.viewer_dict = {}
    await self.accept()

  async def disconnect(self, close_code):
    for mode in self.viewer_dict:
      for idx in self.viewer_dict[mode]:
        dict_item = self.viewer_dict[mode][idx]
        if dict_item['show_cam']:
          dict_item['viewer'].pop_from_onf(dict_item['onf'])
        dict_item['log'].stop = timezone.now()
        dict_item['log'].active = False
        while True:
          try:
            await dict_item['log'].asave(update_fields=["stop", "active", ])
            break
          except OperationalError:
            connection.close()
            
  @staticmethod
  def check_conditions(user, mystream):
    return not (
      user.is_superuser 
      and is_public_server
      and mystream.dbline.encrypted
      and mystream.dbline.creator.id != user.id
    )

  async def receive(self, text_data):
    logger.debug('<-- ' + str(text_data))
    if text_data[0] in {'C', 'D', 'E'}:
      mode = text_data[0]
      idx = int(text_data[1:7])
      self.viewer_dict[mode][idx]['viewer'].clear_busy(int(text_data[7:13]))
      return()
    params = json.loads(text_data)['data']
    outlist = {'tracker' : json.loads(text_data)['tracker']}

    if params['command'] == 'starttrigger':
      if 'do_compress' in params:
        do_compress = params['do_compress']
      else:
        do_compress = True  
      mystream = streams[params['idx']]
      show_cam = await sync_to_async(self.check_conditions)(self.scope['user'], mystream)
      if access.check(params['mode'], params['idx'], self.scope['user'], 'R'):
        outx = params['width']
        if params['mode'] == 'C':
          if outx > mystream.dbline.cam_min_x_view:
            outx *= mystream.dbline.cam_scale_x_view
            outx = max(mystream.dbline.cam_min_x_view, outx)
            if mystream.dbline.cam_max_x_view:
              outx = min(mystream.dbline.cam_max_x_view, outx)
          while not hasattr(mystream, 'mycam'):
            await asyncio.sleep(longbreak)
          myviewer = mystream.mycam.viewer
        elif params['mode'] == 'D':
          mydetector = mystream.mydetector
          while mydetector.scaledown is None:
            await asyncio.sleep(longbreak)
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
        myviewer.websocket = self
        myviewer.event_loop = asyncio.get_event_loop()
        outx = round(min(mystream.dbline.cam_xres, outx))
        if show_cam:
          onf_index = myviewer.push_to_onf(outx, do_compress, self)
        else:
          onf_index = None  
        if params['mode'] not in self.viewer_dict:
          self.viewer_dict[params['mode']] = {}
        self.viewer_dict[params['mode']][params['idx']] = {
          'onf' : onf_index,
          'viewer' : myviewer,
          'show_cam' : show_cam,
        }
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
        await my_log_line.asave()
        self.viewer_dict[params['mode']][params['idx']]['log'] = my_log_line
        outlist['data'] = {
          'outx' : outx, 
          'show_cam' : show_cam,
          'on_frame_nr' : onf_index,
        }
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))
      else:
        await self.close()

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
      go_on = await access.check_async(params['mode'], params['idx'], self.scope['user'], 'R')
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
