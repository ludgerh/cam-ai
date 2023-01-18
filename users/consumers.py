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
from string import ascii_letters, punctuation
from random import choice
from logging import getLogger
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password,  check_password
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tools.c_logger import log_ini
from tools.djangodbasync import getonelinedict, savedbline, getoneline
from users.archive import myarchive, uniquename
from .models import userinfo

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
      
#*****************************************************************************
# usradminConsumer
#*****************************************************************************

class usradminConsumer(AsyncWebsocketConsumer):
  async def connect(self):
    await self.accept()

  async def receive(self, text_data=None, bytes_data=None):
    logger.debug('<-- ' + str(text_data))
    indict=json.loads(text_data)
    if indict['code'] == 'make_usr':
      myclient = await getoneline(client, {'id' : indict['client_nr'], })
      if not check_password(indict['pass'], myclient.hash):
        await self.send(json.dumps(None))
        return()
      try:
        userinfodict = await getonelinedict(userinfo, {'client_nr': indict['client_nr'], }, ['user', ])
      except userinfo.DoesNotExist:
        newuser = User()
        newuser.username = 'RemoteServer'+str(indict['client_nr'])
        await savedbline(newuser)
        newuserinfo = userinfo()
        newuserinfo.user = newuser
        newuserinfo.client_nr = myclient
        await savedbline(newuserinfo)
        result = {'usrid' : newuser.id, 'name' : newuser.username, }
      else:
        newuser = await getoneline(User, {'id' : userinfodict['user'], })
        result = {'usrid' : newuser.id, 'name' : newuser.username, }
      letters = ascii_letters + punctuation
      password = ''.join(choice(letters) for i in range(20))
      passhash = make_password(password)
      newuser.password = passhash
      await savedbline(newuser, ['password', ])
      result['pass'] = password 
      await self.send(json.dumps(result))
