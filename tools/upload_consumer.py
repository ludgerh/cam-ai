"""
Copyright (C) 2025 by the CAM-AI team, info@cam-ai.de
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
import uuid
from logging import getLogger
from traceback import format_exc
from pathlib import Path
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini

LOGNAME = 'ws_uploads'
logger = getLogger(LOGNAME)
log_ini(logger, LOGNAME)

BASE_PATH = Path(settings.BASE_DIR)
PARENTPATH = BASE_PATH.parent
UPLOAD_TMP = PARENTPATH / "temp" / "chunk_ws"
UPLOAD_DST = PARENTPATH / "temp" / "backup"   
UPLOAD_TMP.mkdir(parents=True, exist_ok=True)
UPLOAD_DST.mkdir(parents=True, exist_ok=True) 

class uploads_async_consumer(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      await self.accept()
      self.upload_uid = None
      self.filename = None
      self.tmp_path = None
      self.fp = None
      self.bytes_received = 0
    except:
      logger.error('Error in consumer: ' + LOGNAME + ' (uploads_async_consumer)')
      logger.error(format_exc())
      
  async def disconnect(self, code):
    try:
      if self.fp and not self.fp.closed:
          self.fp.close()
    except:
      logger.error('Error in consumer: ' + LOGNAME + ' (uploads_async_consumer)')
      logger.error(format_exc())
      
  async def receive(self, text_data =None, bytes_data=None):
    try:
      if bytes_data:
        chunk_len = len(bytes_data)
        self.bytes_received += chunk_len
        if self.bytes_received >= self.filesize:
          result = 'Done!'
        else:
          result = str(round(self.bytes_received / self.filesize * 100)) + '%'
        await self.send(result)
        if self.fp:
          self.fp.write(bytes_data)
        else:
          logger.error('binary data ohne upload_start erhalten')
        return()
      #logger.info('<-- ' + text_data)
      params = json.loads(text_data)
      if params['command'] == 'upload_start':	
        self.upload_uid = params.get('id') or str(uuid.uuid4())
        self.filename = Path(params['filename']).name
        self.filesize = params['size']
        self.tmp_path = UPLOAD_TMP / f"{self.upload_uid}.part"
        self.fp = self.tmp_path.open("ab")
        outlist = {
          'status' : 'OK',
          'id' : self.upload_uid,
          'offset' : self.tmp_path.stat().st_size,
        }
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
      elif params['command'] == 'upload_finish':	
        if self.fp and not self.fp.closed:
          self.fp.close()
        dst = (UPLOAD_DST / self.filename)
        self.tmp_path.rename(dst)
        outlist = {
          'status' : 'OK',
          'filename' : dst.name,
        }
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
    except:
      logger.error('Error in consumer: ' + LOGNAME + ' (uploads_async_consumer)')
      logger.error(format_exc())
