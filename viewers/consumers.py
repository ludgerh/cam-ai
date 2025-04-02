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
import asyncio
from logging import getLogger
from traceback import format_exc
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from autobahn.exception import Disconnected
from access.c_access import access
from asgiref.sync import sync_to_async
from globals.c_globals import viewables, viewers
from streams.redis import my_redis as streams_redis
from tools.l_tools import djconf
from tools.c_logger import log_ini
from tools.tokens import checktoken

logname = 'ws_viewers'
logger = getLogger(logname)
log_ini(logger, logname)

longbreak = djconf.getconfigfloat('long_brake', 1.0)
is_public_server = djconf.getconfigbool('is_public_server', False)

#*****************************************************************************
# triggerConsumer
# This is not async because the funtion ONF gets called from Sync
#*****************************************************************************

class triggerConsumer(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      self.viewer_dict = {}
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (trigger)')
      logger.error(format_exc())

  async def disconnect(self, close_code):
    try:
      for mode in self.viewer_dict:
        for idx in self.viewer_dict[mode]:
          #print('Disconnecting', mode, idx)
          dict_item = self.viewer_dict[mode][idx]
          if dict_item['show_cam']:
            dict_item['viewer'].pop_from_onf(dict_item['onf'])
    except:
      logger.error('Error in consumer: ' + logname + ' (trigger)')
      logger.error(format_exc())
            
  @staticmethod
  def check_conditions(user, mystream):
    return not (
      user.is_superuser 
      and is_public_server
      and mystream.dbline.encrypted
      and mystream.dbline.creator.id != user.id
    )

  async def receive(self, text_data):
    try:
      #logger.info('<-- ' + str(text_data))
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
        while not (params['idx'] in viewables and 'stream' in viewables[params['idx']]):
          await asyncio.sleep(longbreak)
        mystream = viewables[params['idx']]['stream']
        show_cam = await sync_to_async(
          self.check_conditions, 
          thread_sensitive=True, 
        )(self.scope['user'], mystream)
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
            myviewer = viewers[params['idx']][params['mode']]
          elif params['mode'] == 'D':
            mydetector = viewables[params['idx']]['D']
            while mydetector.scaledown is None:
              await asyncio.sleep(longbreak)
            if outx > mystream.dbline.det_min_x_view:
              outx *= mystream.dbline.det_scale_x_view
              outx = max(mystream.dbline.det_min_x_view, outx)
              if mystream.dbline.det_max_x_view:
                outx = min(mystream.dbline.det_max_x_view, outx)
              if mydetector.scaledown > 1:
                outx = min(outx, mystream.dbline.cam_xres / mydetector.scaledown)
            myviewer = viewers[params['idx']][params['mode']]
          elif params['mode'] == 'E':
            myeventer = viewables[params['idx']]['E']
            myeventer.inqueue.put(('setdscrwidth', outx, ))
            if outx > mystream.dbline.eve_min_x_view:
              outx *= mystream.dbline.eve_scale_x_view
              outx = max(mystream.dbline.eve_min_x_view, outx)
              if mystream.dbline.eve_max_x_view:
                outx = min(mystream.dbline.eve_max_x_view, outx)
            myviewer = viewers[params['idx']][params['mode']]
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
          outlist['data'] = {
            'outx' : outx, 
            'show_cam' : show_cam,
            'on_frame_nr' : onf_index,
          }
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))
        else:
          await self.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (trigger)')
      logger.error(format_exc())

#*****************************************************************************
# c_viewConsumer
#*****************************************************************************

class c_viewConsumer(AsyncWebsocketConsumer):

  @database_sync_to_async
  def mychecktoken(self, *args):
    return(checktoken(*args))

  async def connect(self):
    try:
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (c_view)')
      logger.error(format_exc())

  async def receive(self, text_data):
    try:
      #logger.info('<-- ' + str(text_data))
      params = json.loads(text_data)['data']
      outlist = {'tracker' : json.loads(text_data)['tracker']}

      if params['command'] == 'getcaminfo':
        go_on = await access.check_async(params['mode'], params['idx'], self.scope['user'], 'R')
        if go_on:
          outlist['data'] = {}
          outlist['data']['fps'] = round(streams_redis.fps_from_dev(params['mode'], params['idx'], ), 2, )
          outlist['data']['viewers'] = streams_redis.view_from_dev(params['mode'], params['idx'], )
          logger.debug('--> ' + str(outlist))
          try:
            await self.send(json.dumps(outlist))	
          except Disconnected:
            logger.warning('*** Could not send Cam Info , socket closed...')
        else:
          await self.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (c_view)')
      logger.error(format_exc())
