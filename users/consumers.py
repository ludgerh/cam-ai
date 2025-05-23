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
from django.conf import settings
from channels.generic.websocket import WebsocketConsumer #, AsyncWebsocketConsumer
from tools.c_logger import log_ini
from tools.tokens import maketoken
from users.archive import myarchive
from .models import archive as dbarchive
from .userinfo import free_quota

logname = 'ws_users'
logger = getLogger(logname)
log_ini(logger, logname)
      
#*****************************************************************************
# archiveConsumer
#*****************************************************************************

class archiveConsumer(WebsocketConsumer):

  def connect(self):
    try:
      self.user = self.scope['user']
      self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (archive)')
      logger.error(format_exc())

  def to_archive(self, mytype, mynumber):
    myarchive.to_archive(mytype, mynumber, self.scope['user'])

  def check_archive(self, mytype, mynumber):
    if free_quota(self.scope['user']):
      return(myarchive.check_archive(mytype, mynumber, self.scope['user']))
    else:
      return(True)  

  def del_archive(self, mynumber):
    myarchive.del_archive(mynumber, self.scope['user'])

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

  def receive(self, text_data=None, bytes_data=None):
    try:
      logger.debug('<-- ' + str(text_data))
      inlist = json.loads(text_data)
      params = inlist['data']
      outlist = {'tracker' : inlist['tracker']}
      if params['command'] == 'to_arch':
        self.to_archive(params['type'], int(params['frame_nr']))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        self.send(json.dumps(outlist))
      elif params['command'] == 'check_arch':
        outlist['data'] = self.check_archive(params['type'], int(params['frame_nr']))
        logger.debug('--> ' + str(outlist))
        self.send(json.dumps(outlist))
      elif params['command'] == 'del_arch':
        self.del_archive(params['line_nr'])
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        self.send(json.dumps(outlist))
      elif params['command'] == 'get_dl_url':
        outlist['data'] = self.get_dl_url(params['line_nr'])
        logger.debug('--> ' + str(outlist))
        self.send(json.dumps(outlist))
    except:
      logger.error('Error in consumer: ' + logname + ' (archive)')
      logger.error(format_exc())
