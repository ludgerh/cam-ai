"""
Copyright (C) 2024-2026 by the CAM-AI team, info@cam-ai.de
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
import struct
from logging import getLogger
from traceback import format_exc
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async, aclose_old_connections
from autobahn.exception import Disconnected
from access.c_access import access
from globals.c_globals import viewables, viewers
from streams.redis import my_redis as streams_redis
from streams.models import stream
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
      await aclose_old_connections()
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (trigger)')
      logger.error(format_exc())

  async def disconnect(self, code = None):
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
  def check_conditions(user, dbline):
    return not (
      user.is_superuser 
      and is_public_server
      and dbline.encrypted
      and dbline.creator.id != user.id
    )

  async def receive(self, text_data=None, bytes_data=None):
    try:
      if bytes_data is not None:
        #logger.info('<-- ' + str(bytes_data))
        mode = chr(bytes_data[0])
        idx, count = struct.unpack('<2I', bytes_data[1:9])
        self.viewer_dict[mode][idx]['viewer'].clear_busy(count)
        return()
        
      params = json.loads(text_data)['data']
      outlist = {'tracker' : json.loads(text_data)['tracker']}
      #logger.info('<-- ' + str(text_data))
      
      if params['command'] == 'starttrigger':
        if 'do_compress' in params:
          do_compress = params['do_compress']
        else:
          do_compress = True  
        while not (params['idx'] in viewables and 'stream' in viewables[params['idx']]):
          await asyncio.sleep(longbreak)
        mystream = viewables[params['idx']]['stream']
        dbline = await stream.objects.aget(id = params['idx'])
        show_cam = await database_sync_to_async(self.check_conditions)(
          self.scope['user'], 
          dbline,
        )
        if access.check(params['type'], params['idx'], self.scope['user'], 'R'):
          if 'width' in params:
            x_canvas = params['width']
          else:  
            x_canvas = params['x_screen'] - 60
          if params['type'] == 'C':
            y_canvas =  round(x_canvas * dbline.cam_yres / dbline.cam_xres)
            outx = min(x_canvas, round(dbline.cam_xres / dbline.cam_scaledown))
            outy = min(y_canvas, round(dbline.cam_yres / dbline.cam_scaledown))
            x_scaling = dbline.cam_xres / x_canvas
            y_scaling = dbline.cam_yres / y_canvas   
          elif params['type'] in {'D', 'E'}:
            y_canvas = -1
            outx = -1
            outy = -1
            x_scaling = -1.0
            y_scaling = -1.0
          myviewer = viewers[params['idx']][params['type']]
          myviewer.websocket = self
          myviewer.event_loop = asyncio.get_event_loop()
          if show_cam:
            onf_index = myviewer.push_to_onf(
              outx = outx, 
              outy = outy, 
              x_canvas = x_canvas,
              y_canvas = y_canvas,
              x_scaling = x_scaling,
              y_scaling = y_scaling,
              do_compress = do_compress, 
              websocket = self, 
            )
          else:
            onf_index = None  
          if params['type'] not in self.viewer_dict:
            self.viewer_dict[params['type']] = {}
          self.viewer_dict[params['type']][params['idx']] = {
            'onf' : onf_index,
            'viewer' : myviewer,
            'show_cam' : show_cam,
          }
          if self.scope['user'].is_authenticated:
            myuser = self.scope['user'].id
          else:
            myuser = -1
          outlist['data'] = {
            'show_cam' : show_cam,
            'on_frame_nr' : onf_index,
          }
          #logger.info('--> ' + str(outlist))
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

  async def connect(self):
    try:
      await aclose_old_connections()
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
        go_on = await access.check_async(
          params['type'], 
          params['idx'], 
          self.scope['user'], 
          'R', 
        )
        if go_on:
          outlist['data'] = {}
          outlist['data']['fps'] = round(
            streams_redis.fps_from_dev(params['type'], params['idx'], ), 
            2, 
          )
          outlist['data']['viewers'] = streams_redis.view_from_dev(
            params['type'], 
            params['idx'], 
          )
          if params['type'] in {'D', 'E'}:
            myitem = viewables[params['idx']][params['type']]
            try:
              outlist['data']['xdim'] = myitem.shared_mem.read_1_meta('aoi_xdim')
              outlist['data']['ydim'] = myitem.shared_mem.read_1_meta('aoi_ydim')
            except TypeError:
              pass  
          #logger.info('--> ' + str(outlist))
          try:
            await self.send(json.dumps(outlist))	
          except Disconnected:
            logger.warning('*** Could not send Cam Info , socket closed...')
        else:
          await self.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (c_view)')
      logger.error(format_exc())
