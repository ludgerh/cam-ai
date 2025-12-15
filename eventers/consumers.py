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
from logging import getLogger
from traceback import format_exc
from django.db import close_old_connections
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini
from .models import alarm as dbalarm

logname = 'ws_eventers'
logger = getLogger(logname)
log_ini(logger, logname)

class alarm(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      if self.scope['user'].is_superuser:
        self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (alarm)')
      logger.error(format_exc())
      
  async def disconnect(self, code = None): 
    close_old_connections()       

  async def receive(self, text_data):
    try:
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	
      print(text_data)

      if params['command'] == 'write_db':
        alarmline = dbalarm(name='test', mendef='text',action_type=1,action_param1='t',
          action_param2='t')
        await alarmline.asave()
        outlist['data'] = 'OK'
        print('--> ' + str(outlist))
        await self.send(json.dumps(outlist))
    except:
      logger.error('Error in consumer: ' + logname + ' (alarm)')
      logger.error(format_exc())
