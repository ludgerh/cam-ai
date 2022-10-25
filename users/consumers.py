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
from logging import getLogger
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tools.c_logger import log_ini
from users.archive import myarchive, uniquename

logname = 'ws_usersconsumers'
logger = getLogger(logname)
log_ini(logger, logname)
      
#*****************************************************************************
# archiveConsumer
#*****************************************************************************

class archiveConsumer(AsyncWebsocketConsumer):
  async def connect(self):
    self.user = self.scope['user']
    await self.accept()

  @database_sync_to_async
  def to_archive(self, mytype, mynumber):
    myarchive.to_archive(mytype, mynumber, self.scope['user'].id)

  @database_sync_to_async
  def check_archive(self, mytype, mynumber):
    return(myarchive.check_archive(mytype, mynumber, self.scope['user'].id))

  async def receive(self, text_data=None, bytes_data=None):
    logger.debug('<-- ' + str(text_data))
    inlist = json.loads(text_data)
    params = inlist['data']
    outlist = {'tracker' : inlist['tracker']}
    if params['command'] == 'to_arch':
      await self.to_archive(params['type'], int(params['frame_nr']))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))
    elif params['command'] == 'check_arch':
      outlist['data'] = await self.check_archive(params['type'], int(params['frame_nr']))
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))
