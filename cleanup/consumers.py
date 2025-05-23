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
from pathlib import Path
from time import sleep
from threading import Lock as t_lock
from logging import getLogger
from traceback import format_exc
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini
from tools.l_tools import djconf
from tf_workers.models import school
from trainers.models import trainframe
from eventers.models import event, event_frame
from .c_cleanup import my_cleanup
from .redis import my_redis as cleanup_redis
#from .redis import get_from_redis, get_from_redis_queue, len_from_redis_queue
from .models import files_to_delete

logname = 'ws_cleanup'
logger = getLogger(logname)
log_ini(logger, logname)
datapath = djconf.getconfig('datapath', 'data/')
recordingspath = Path(djconf.getconfig('recordingspath', datapath + 'recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', datapath + 'schoolframes/'))

#*****************************************************************************
# cleanup
#*****************************************************************************

class cleanup(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      if self.scope['user'].is_superuser:
        self.missingdbdict= {}
        self.missingfilesdict = {}
        self.counter_lock = t_lock()
        await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (cleanup)')
      logger.error(format_exc())

  async def receive(self, text_data):
    try:
      logger.debug('<-- ' + text_data)
      params = json.loads(text_data)['data']	
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

      if self.scope['user'].is_superuser:

        if params['command'] == 'checkevents':
          outlist['data'] = {
            'events_temp' : len_from_redis_queue('events_temp', params['stream']),
            'events_frames_correct' : get_from_redis('events_frames_correct', params['stream']),
            'events_frames_missingframes' : len_from_redis_queue('events_frames_missingframes', params['stream']),
            'eframes_correct' : get_from_redis('eframes_correct', params['stream']),
            'eframes_missingdb' : len_from_redis_queue('eframes_missingdb', params['stream']),
            'eframes_missingfiles' : len_from_redis_queue('eframes_missingfiles', params['stream']),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_events_temp':		
          list_to_delete = get_from_redis_queue('events_temp', params['stream'])
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            eventline = await event.objects.aget(id=int(item))
            eventline.deleted = True
            await eventline.asave(update_fields = ['deleted'])
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          if 'callback' in outlist:
            del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_events_frames_missingframes':		
          list_to_delete = get_from_redis_queue('events_frames_missingframes', params['stream'])
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            eventline = await event.objects.aget(id=int(item))
            eventline.deleted = True
            await eventline.asave(update_fields = ['deleted'])
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_eframes_missingdb':	
          list_to_delete = get_from_redis_queue('eframes_missingdb', params['stream'])
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            del_line = files_to_delete(name = schoolframespath / item.decode(), min_age = 300)
            await del_line.asave()
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_eframes_missingfiles':	
          list_to_delete = get_from_redis_queue('eframes_missingfiles', params['stream'])
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            eframe_line = await event_frame.objects.aget(name = item.decode())
            eframe_line.deleted = True
            await eframe_line.asave(update_fields = ['deleted'])
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'checkschool':
          outlist['data'] = {
            'schools_correct' : get_from_redis('schools_correct', params['school']),
            'schools_missingdb' : len_from_redis_queue('schools_missingdb', params['school']),
            'schools_missingfiles' : len_from_redis_queue('schools_missingfiles', params['school']),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_schools_missingdb':	
          school_line = await school.objects.aget(id=params['school'])
          myschooldir = school_line.dir
          list_to_delete = get_from_redis_queue('schools_missingdb', params['school'])
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            del_line = files_to_delete(name = school_line.dir + '/frames/' + item.decode() + '.bmp', min_age = 300)
            await del_line.asave()
            for dim in my_cleanup.model_dims[params['school']]:
              del_line = files_to_delete(name = school_line.dir + '/coded/' + dim + '/' + item.decode() + '.cod', min_age = 300)
              await del_line.asave()
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_schools_missingfiles':	
          list_to_delete = get_from_redis_queue('schools_missingfiles', params['school'])
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            frame_line = await trainframe.objects.aget(
              name = item.decode() + '.bmp',
              school = params['school'], 
            )
            frame_line.deleted = True
            await frame_line.asave(update_fields = ['deleted'])
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'checkrecfiles':
          outlist['data'] = {
            'videos_correct' : get_from_redis('videos_correct', 0),
            'videos_missingdb' : len_from_redis_queue('videos_missingdb', 0),
            'videos_missingfiles' : len_from_redis_queue('videos_missingfiles', 0),
            'videos_temp' : len_from_redis_queue('videos_temp', 0),
            'videos_mp4' : get_from_redis('videos_mp4', 0),
            'videos_webm' : get_from_redis('videos_webm', 0),
            'videos_jpg' : get_from_redis('videos_jpg', 0),
          }
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_videos_temp':	
          list_to_delete = get_from_redis_queue('videos_temp', 0)
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            del_line = files_to_delete(name = recordingspath / item.decode())
            await del_line.asave()
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_videos_missingdb':	
          list_to_delete = get_from_redis_queue('videos_missingdb', 0)
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            for ext in ['.jpg', '.mp4', '.webm']:
              delpath = recordingspath / (item.decode() + ext)
              del_line = files_to_delete(name = delpath, min_age = 300)
              await del_line.asave()
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	

        elif params['command'] == 'fix_videos_missingfiles':	
          list_to_delete = get_from_redis_queue('videos_missingfiles', 0)
          counter = len(list_to_delete)
          counter_start = len(list_to_delete)
          for item in list_to_delete:
            eventlines = event.objects.filter(videoclip=item.decode())
            async for eventline in eventlines:
              eventline.videoclip=''
              await eventline.asave(update_fields = ['videoclip'])
            for ext in ['.jpg', '.mp4', '.webm']:
              delpath = recordingspath / (item.decode() + ext)
              del_line = files_to_delete(name = delpath, min_age = 300)
              await del_line.asave()
            outlist['callback'] = True
            outlist['data'] = '(' + str(counter) + '/' + str(counter_start) + ')'
            logger.debug('--> ' + str(outlist))
            await self.send(json.dumps(outlist))	
            with self.counter_lock:
              counter -= 1
          self.counter_lock.acquire()
          while counter:
            self.counter_lock.release()
            sleep(1.0)   
            self.counter_lock.acquire() 
          self.counter_lock.release()
          del outlist['callback']
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))	
            
      else:
        await self.close()
    except:
      logger.error('Error in consumer: ' + logname + ' (cleanup)')
      logger.error(format_exc())
