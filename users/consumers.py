# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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
from string import ascii_letters, punctuation
from random import choice
from logging import getLogger
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password,  check_password
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tools.c_logger import log_ini
from tools.tokens import maketoken
from tools.djangodbasync import getonelinedict, savedbline, getoneline
from users.archive import myarchive, uniquename
from .models import userinfo, archive as dbarchive

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
    myarchive.to_archive(mytype, mynumber, self.scope['user'])

  @database_sync_to_async
  def check_archive(self, mytype, mynumber):
    return(myarchive.check_archive(mytype, mynumber, self.scope['user']))

  @database_sync_to_async
  def del_archive(self, mynumber):
    myarchive.del_archive(mynumber, self.scope['user'])

  @database_sync_to_async
  def get_dl_url(self, mynumber):
    archiveline = dbarchive.objects.get(id=mynumber)
    mytoken = maketoken('ADL', mynumber, 'Download from Archive #'+str(mynumber))
    dlurl = settings.CLIENT_URL
    dlurl += 'users/downarchive/'
    dlurl += str(mynumber) + '/' + str(mytoken[0]) + '/' + mytoken[1] +'/'
    if archiveline.typecode == 0:
      dlurl += 'image.bmp'
    elif archiveline.typecode == 1:
      dlurl += 'video.mp4'
    return(dlurl)

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
    elif params['command'] == 'del_arch':
      await self.del_archive(params['line_nr'])
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))
    elif params['command'] == 'get_dl_url':
      outlist['data'] = await self.get_dl_url(params['line_nr'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))
