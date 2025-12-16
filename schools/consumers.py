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
import numpy as np
import cv2 as cv
import asyncio
import aiofiles
import aiofiles.os
import aioshutil
import aiohttp
from asgiref.sync import sync_to_async
from glob import glob
from os import path
from random import randint
from logging import getLogger
from traceback import format_exc
from datetime import datetime
from collections import defaultdict
from time import time
from django.utils import timezone
from django.contrib.auth.models import User as dbuser
from django.core.paginator import Paginator
from django.db import close_old_connections
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async, close_old_connections
from django.contrib.auth.hashers import check_password
from camai.c_settings import safe_import
from tools.l_tools import ts2filename, djconf, uniquename_async
from tools.c_tools import reduce_image_async
from tools.c_logger import log_ini
from tools.l_crypt import l_crypt
from tools.l_break import a_break_type, BR_LONG
from access.c_access import access
from access.models import access_control
from globals.c_globals import tf_workers
from schools.c_schools import get_taglist, check_extratags_async
from schools.views import getbmp_dict
from tf_workers.models import school, worker
from tf_workers.c_tf_workers import tf_worker_client
from eventers.models import event, event_frame
from trainers.models import trainframe, trainer
from trainers.redis import my_redis as trainers_redis
from users.models import userinfo
from streams.models import stream
from trainers.redis import my_redis as trainers_redis

mydomain = safe_import('mydomain') 

logname = 'ws_schools'
logger = getLogger(logname)
log_ini(logger, logname)
classes_list = get_taglist(1)
datapath = djconf.getconfig('datapath', 'data/')
schoolframespath = djconf.getconfig('schoolframespath', datapath + 'schoolframes/')
recordingspath = djconf.getconfig('recordingspath', datapath + 'recordings/')
schoolsdir = djconf.getconfig('schools_dir', datapath + 'schools/')
school_x_max = djconf.getconfigint('school_x_max', 500)
school_y_max = djconf.getconfigint('school_y_max', 500)

if mydomain:
  myserver = mydomain
else:
  myserver = 'localhost'  

#*****************************************************************************
# SchoolDBUtil
#*****************************************************************************

CHUNK_SIZE = 32

def decode_and_convert_image(myimage_bytes):
  img = cv.imdecode(np.frombuffer(myimage_bytes, dtype=np.uint8), cv.IMREAD_UNCHANGED)
  return cv.cvtColor(img, cv.COLOR_BGR2RGB)

def _chunked(seq, n):
  for i in range(0, len(seq), n):
    yield seq[i:i+n]


@database_sync_to_async
def get_framelines(event_id):
  return list(event_frame.objects.filter(event__id=event_id).order_by('time', 'id'))

class schooldbutil(AsyncWebsocketConsumer):

  cache_dict = {}
  cache_dict['tagging'] = defaultdict(dict)
  cache_dict['school'] = defaultdict(dict)
  school_lines = {}
  consumer_id_list = []

  @database_sync_to_async
  def gettags(self, myschool):
    return([line.description for line in get_taglist(myschool)])

  @database_sync_to_async
  def gettrainshortlist(self, page_nr):
    return(list(self.trainpage.get_elided_page_range(page_nr)))

  @database_sync_to_async
  def geteventshortlist(self, page_nr):
    return(list(self.eventpage.get_elided_page_range(page_nr)))
    
  @database_sync_to_async  
  def gettrainobjectlist(self, page_nr):
    page = self.trainpage.get_page(page_nr)
    return list(page.object_list) 

  async def connect(self):
    try:
      global getbmp_dict
      self.check_ts = 0.0
      self.user = self.scope['user']
      self.tf_w_index = None
      if self.user.is_authenticated:
        await self.accept()
      else:
        await self.close()
      self.consumer_id = 0
      while self.consumer_id in schooldbutil.consumer_id_list:
        self.consumer_id += 1
      schooldbutil.consumer_id_list.append(self.consumer_id)  
      getbmp_dict.setdefault(0, {})
      getbmp_dict[0][self.consumer_id] = {}
      getbmp_dict.setdefault(1, {})
      getbmp_dict[1][self.consumer_id] = {}
    except:
      logger.error('Error in consumer: ' + logname + ' (schooldbutil)')
      logger.error(format_exc())

  async def disconnect(self, close_code):
    try:
      if self.tf_w_index is not None:
        await self.tf_worker.stop_out(self.tf_w_index)
        await self.tf_worker.unregister(self.tf_w_index) 
      close_old_connections()   
      del getbmp_dict[0][self.consumer_id]
      del getbmp_dict[1][self.consumer_id]
      schooldbutil.consumer_id_list.remove(self.consumer_id) 
    except:
      logger.error('Error in consumer: ' + logname + ' (schooldbutil)')
      logger.error(format_exc())
      
  async def predictions_from_tfw(self, frames, school_nr, is_tagger):
    school_dbline = self.school_lines[school_nr]
    i_global = 0  # for periodic sleep()
    cancelled = False
    for chunk in _chunked(frames, CHUNK_SIZE):
      imglist = []
      code_list = []
      frame_ids = []
      for item in chunk:
        try:
          # Periodical release of eventloop for ping/pong
          if i_global % 3 == 0:
            await asyncio.sleep(0)
          if is_tagger:
            my_cache_dict = schooldbutil.cache_dict['tagging']
            use_ram_cache = (
              item['idx'] in my_cache_dict
              and my_cache_dict[item['idx']]['fit'] == school_dbline.last_fit
            )
            frameline = await event_frame.objects.aget(id=item['idx'])
            imagepath = schoolframespath + frameline.name
          else:
            my_cache_dict = schooldbutil.cache_dict['school']
            use_ram_cache = (
              item['idx'] in my_cache_dict
              and my_cache_dict[item['idx']]['fit'] == school_dbline.last_fit
            )
            frameline = await trainframe.objects.aget(id=item['idx'])
            imagepath = school_dbline.dir + 'frames/' + frameline.name 
          frame_ids.append(frameline.id)
          if use_ram_cache:
            code_list.append('R')
          else: 
            if not is_tagger and frameline.last_fit == school_dbline.last_fit:
              code_list.append('D')
            else: 
              try:
                async with aiofiles.open(imagepath, mode = "rb") as f:
                  myimage = await f.read()
                if frameline.encrypted:
                  myimage = self.crypt.decrypt(myimage) 
                myimage = await asyncio.to_thread(decode_and_convert_image, myimage)  
                imglist.append(myimage)
                code_list.append('I')
              except FileNotFoundError:
                logger.warning(
                  f'SC{school_nr}: {imagepath} not found'
                )  
                code_list.append('0')
        except FileNotFoundError:
          logger.error('*** File not found: %s', imagepath)
          raise  # lasse den Fehler nach oben gehen
        except asyncio.CancelledError:
          cancelled = True
          raise
        finally:
          if cancelled:
            logger.info(
              f'SC{school_nr}: {imagepath}: Getpredictions cancelled (client disconnect)'
            )  
          i_global += 1
      await self.tf_worker.ask_pred(
        school_nr, 
        imglist, 
        self.tf_w_index,
      )
      received = []
      for code, frame_dict, frame_id in zip(code_list, chunk, frame_ids):
        if code == 'I':
          try:
            if not received:
              received = (await asyncio.wait_for(
                self.tf_worker.get_from_outqueue(self.tf_w_index),
                timeout=60
              )).tolist()
            prediction = received.pop(0)  
            frame_dict['prediction'] = prediction
            cache_entry = my_cache_dict.setdefault(frame_id, {})
            cache_entry['pred'] = prediction
            cache_entry['fit'] = school_dbline.last_fit
          except asyncio.TimeoutError:
            logger.error(
              f'SC{school_nr}: Timeout during Getpredictions'
            )  
            frame_dict['prediction'] = None
        elif code == 'R':
          frame_dict['prediction'] = my_cache_dict[frame_id]['pred']
        elif code == 'D':
          frameline = await trainframe.objects.aget(id=frame_id)
          frame_dict['prediction'] = tuple(
              getattr(frameline, f"pred{i}") for i in range(10)
            )
          cache_entry = my_cache_dict.setdefault(frame_id, {})
          cache_entry['pred'] = frame_dict['prediction']
          cache_entry['fit'] = school_dbline.last_fit
        elif code == '0':  
          frame_dict['prediction'] = None
    return() 

  async def receive(self, text_data):
    try:
      global getbmp_dict
      #logger.info('<-- ' + text_data)
      params = json.loads(text_data)['data']

      if ((params['command'] == 'gettags') 
          or self.scope['user'].is_authenticated):
        outlist = {'tracker' : json.loads(text_data)['tracker']}
      else:
        await self.close()

      if params['command'] == 'get_consumer_id':
        outlist['data'] = self.consumer_id
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      if params['command'] == 'event_to_dict':
        event_line = await event.objects.select_related('camera').aget(
          id=params['event_nr'], 
        )
        stream_line = event_line.camera
        framelines = await get_framelines(params['event_nr'])
        frame_info = getbmp_dict[0][self.consumer_id]
        if stream_line.crypt_key:
          cryptic = stream_line.crypt_key
        else:
          cryptic =''   
        for item in framelines:
          frame_info.setdefault(item.id, {
            'path': item.name,
            'stream': stream_line.id,
            'crypt' : cryptic,
          })
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'settrainpage':
        school_nr = params['school_nr']
        if self.check_ts + 60.0 < time():
          await self.school_lines[school_nr].arefresh_from_db()
          self.check_ts = time()
        filterdict = {
          'school' : school_nr,
          'deleted' : False,
        }
        if params['cbnot']:
          if not params['cbchecked']:
            filterdict['checked'] = 0
        else:
          if params['cbchecked']:
            filterdict['checked'] = 1
          else:
            filterdict['checked'] = -1 #Never
        if params['class'] == -2:
          pass
        elif params['class'] == -1:
          for i in range(0,10):
            filterdict['c'+str(i)] = 0
        else:
          filterdict['c'+str(params['class'])] = 1
        framelines = trainframe.objects.filter(**filterdict)
        if params ['cbdifferences']:
          BATCH = 1000
          last_pk = 0
          frames = []
          frames_to_infer = []
          while True:
            qs = (framelines
              .filter(pk__gt=last_pk)
              .order_by("pk")[:BATCH])
            batch = await sync_to_async(list)(qs)
            if not batch:
              break
            for item in batch:
              frame = {
                "idx": item.id,
                "line": item,
                "tags": tuple(getattr(item, f"c{i}") for i in range(10)),
              }
              if item.last_fit != self.school_lines[school_nr].last_fit:
                frames_to_infer.append(frame)
              else:
                frame["prediction"] = tuple(getattr(item, f"pred{i}") for i in range(10))
              frames.append(frame)
              last_pk = item.id
            await sync_to_async(close_old_connections)()
          await self.predictions_from_tfw(
            frames_to_infer, 
            school_nr, 
            False, 
          )
          for item in frames_to_infer:
            item['line'].last_fit = self.school_lines[school_nr].last_fit
            if item['prediction']:
              for i in range(10):
                setattr(item['line'], f"pred{i}", item['prediction'][i])
            await item['line'].asave(
              update_fields=["last_fit"] + [f"pred{i}" for i in range(10)], 
            )
          framelines = []
          for item in frames:
            for i in range(10):
              if item['prediction'] and item['tags'][i] != round(item['prediction'][i]):
                framelines.append(item['line'])
                break
        self.trainpage = Paginator(framelines, params['pagesize'])
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'seteventpage':
        stream_line = await stream.objects.aget(id=params['streamnr'])
        if params['showdone']:
          eventlines = event.objects.filter(
            camera=params['streamnr'], 
            xmax__gt=-1, 
            deleted=False,
          ).order_by('-id')
        else:  
          eventlines = event.objects.filter(
            camera=params['streamnr'], 
            done=False, 
            xmax__gt=-1,
            deleted=False,
          ).order_by('-id')
        self.eventpage = Paginator(eventlines, params['pagesize'])
        self.stream_nr = params['streamnr']
        if stream_line.encrypted:
          self.crypt_key = stream_line.crypt_key
        else:
          self.crypt_key = ''  
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'gettrainimages':
        lines = []
        for line in await self.gettrainobjectlist(params['page_nr']):
          made_by_nr = await database_sync_to_async(
            lambda: line.made_by)()
          if made_by_nr is None:
            made_by = ''
          else:
            made_by = made_by_nr.username
          lines.append({
            'id' : line.id, 
            'name' : line.name, 
            'made_by' : made_by,
            'cs' : [line.c0,line.c1,line.c2,line.c3,line.c4,line.c5,line.c6,
              line.c7,line.c8,line.c9,],
            'made' : line.made.strftime("%d.%m.%Y %H:%M:%S %Z"),
          })
          getbmp_dict[1][self.consumer_id].setdefault(line.id, {
            'path' : self.school_dir + '*****/' + line.name,
            'school' :self.myschool,
          })
        outlist['data'] = lines
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'getevents':
        lines = []
        async for line in self.eventpage.page(params['page_nr']).object_list:
          lines.append({
            'id' : line.id, 
            'p_string' : line.p_string, 
            'done' : line.done,
            'start' : line.start.strftime("%d.%m.%Y %H:%M:%S"),
            'end' : line.end.strftime("%d.%m.%Y %H:%M:%S"),
            'numframes' : line.numframes,
            'videoclip' : line.videoclip,
            'xmin' : line.xmin,
            'xmax' : line.xmax,
            'ymin' : line.ymin,
            'ymax' : line.ymax,
          })
        outlist['data'] = lines
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'gettrainshortlist':
        result = list(await self.gettrainshortlist(params['page_nr']))
        for i in range(len(result)):
          if not isinstance(result[i], int):
            result[i] = 0
        outlist['data'] = result
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'geteventshortlist':
        result = list(await self.geteventshortlist(params['page_nr']))
        for i in range(len(result)):
          if not isinstance(result[i], int):
            result[i] = 0
        outlist['data'] = result
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'gettags':
        outlist['data'] = await self.gettags(params['school'])
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'getpredictions':
        if await access.check_async('S', params['school'], self.scope['user'], 'R'):
          frames = params['frames']
          if params['is_tagger']:
            await self.predictions_from_tfw(
              frames, 
              params['school'], 
              True, 
            )
            outlist['data'] = ([params['count'], frames])
          else:  
            await self.predictions_from_tfw(
              frames, 
              params['school'], 
              False, 
            )
            outlist['data'] = frames
          #logger.info('--> ' + str(outlist))
          await self.send(json.dumps(outlist))

      elif params['command'] == 'checktrainframe':
        frameline = await trainframe.objects.aget(id=params['img'],)
        if await access.check_async('S', frameline.school, self.user, 'W'):
          frameline.checked = True
          await frameline.asave(update_fields=('checked', ))
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))

      elif params['command'] == 'deltrainframe':
        frameline = await trainframe.objects.aget(id=params['img'],)
        if await access.check_async('S', params['school'], self.user, 'W'):
          frameline.deleted = True
          await frameline.asave(update_fields=('deleted', ))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'checkall':
        if await access.check_async('S', params['school'], self.user, 'W'):
          filterdict = {'school' : params['school']}
          if params['class'] == -2:
            pass
          elif params['class'] == -1:
            for i in range(0,len(classes_list)):
              filterdict['c'+str(i)] = 0
          else:
            filterdict['c'+str(params['class'])] = 1
          filterdict['id__gte'] = params['min_id']
          filterdict['id__lte'] = params['max_id']
          framelines = trainframe.objects.filter(**filterdict)
          #import pdb; pdb.set_trace()
          await framelines.aupdate(checked=1)
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))

      elif params['command'] == 'deleteall':
        if await access.check_async('S', params['school'], self.user, 'W'):
          filterdict = {'school' : params['school']}
          if params['class'] == -2:
            pass
          elif params['class'] == -1:
            for i in range(0,10):
              filterdict['c'+str(i)] = 0
          else:
            filterdict['c'+str(params['class'])] = 1
          filterdict['id__gte'] = params['min_id']
          filterdict['id__lte'] = params['max_id']
          if params['cbnot']:
            if params['cbchecked']:
              pass
            else:
              filterdict['checked'] = 0
          else:
            if params['cbchecked']:
              filterdict['checked'] = 1
            else:
              filterdict = None
          if filterdict is not None:
            framelines = trainframe.objects.filter(**filterdict)
            async for frameline in framelines:
              frameline.deleted = True
              await frameline.asave(update_fields=('deleted', ))
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))

      elif params['command'] == 'copyall':
        # disabled. need check before being reactivated
        if access.check('S', params['school'], self.user, 'W'):
          filterdict = {'school' : params['school']}
          if params['class'] == -2:
            pass
          elif params['class'] == -1:
            for i in range(0,10):
              filterdict['c'+str(i)] = 0
          else:
            filterdict['c'+str(params['class'])] = 1
          filterdict['id__gte'] = params['min_id']
          filterdict['id__lte'] = params['max_id']
          if params['cbnot']:
            if params['cbchecked']:
              pass
            else:
              filterdict['checked'] = 0
          else:
            if params['cbchecked']:
              filterdict['checked'] = 1
            else:
              filterdict = None
          if filterdict is not None:
            school_line = await school.objects.aget(id = params['school'])
            sourcepath = school_line.dir
            school_line = await school.objects.aget(id = 1)
            destpath = school_line.dir
            query_for_copy = await trainframe.objects.filter(**filterdict)
            async for item in query_for_copy:
              if not (await check_extratags_async(params['school'], item)):
                destfilename = uniquename(destpath, path.splitext(item['name'])[0], 'bmp')  
                await aioshutil.copy(sourcepath + 'frames/' + item['name'], destpath + 'frames/' + destfilename)
                newitem = trainframe(made = item['made'],
                  school = 1,
                  name = destfilename,
                  code = 'NE',
                  c0 = item['c0'], c1 = item['c1'], c2 = item['c2'], c3 = item['c3'], 
                  c4 = item['c4'], c5 = item['c5'], c6 = item['c6'], c7 = item['c7'], 
                  c8 = item['c8'], c9 = item['c9'], 
                  checked = False, made_by_id = item['made_by'],
                  img_sizes = item['img_sizes'],
                )
                await newitem.asave()
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))

      elif params['command'] == 'register_ai':
        self.myschool = int(params['school'])
        if self.myschool not in self.school_lines:
          self.school_lines[self.myschool] = await school.objects.aget(id = self.myschool)
          self.check_ts = time()
        self.school_dir = self.school_lines[self.myschool].dir
        if ('logout' in params) and params['logout'] and (self.myschool > 0):
          await self.disconnect()
        if self.myschool > 0:
          schoolline = await school.objects.aget(id=self.myschool)
          workerline = await worker.objects.aget(school__id=schoolline.id)
          self.tf_worker = tf_workers[workerline.id]
          self.tf_worker = tf_worker_client(self.tf_worker.inqueue, self.tf_worker.registerqueue, )
          self.tf_w_index = await self.tf_worker.register(workerline.id)
          await self.tf_worker.run_out(self.tf_w_index, logger, logname)
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'geteventframes':
        framelines = await get_framelines(params['event'])
        result = []
        for item in framelines:
          result.append(item.id)
          getbmp_dict[0][self.consumer_id].setdefault(item.id, {
            'path' : item.name,
            'stream' : self.stream_nr,
            'crypt' : self.crypt_key,
          })
        result = [item.id for item in framelines]
        outlist['data'] = (params['count'], result)
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'setcrypt':
        streamline = await stream.objects.aget(id=params['stream'])
        if streamline.encrypted:
          self.crypt =  l_crypt(key=streamline.crypt_key)
        else:
          self.crypt = None  
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

      elif params['command'] == 'settags':
        schoolline = await school.objects.aget(id=params['school'])
        modelpath = schoolline.dir
        if await access.check_async('S', params['school'], self.scope['user'], 'W'):
          for i in range(100):
            pathadd = str(i) + '/'
            await aiofiles.os.makedirs(modelpath + 'frames/' + pathadd, exist_ok=True)
          eventline = await event.objects.aget(id=params['event'])
          framelines = event_frame.objects.filter(event=eventline).order_by('time', 'id') 
          i = 0
          async for item in framelines:
            pathadd = str(randint(0,99)) + '/'
            ts = datetime.timestamp(item.time)
            newname = await uniquename_async(
              modelpath + 'frames/', 
              pathadd + ts2filename(ts, noblank=True), 
              'bmp', 
            )
            if eventline.done:
              t = await trainframe.objects.aget(id=item.trainframe)
              updatelist = []
              for j in range(10):
                tagname = 'c'+str(j)
                updatelist.append(tagname)
                setattr(item, tagname, params['cblist'][i][j])
              await t.asave(update_fields=updatelist)
            else:
              if item.encrypted:
                do_crypt = self.crypt
              else:
                do_crypt = None   
              await reduce_image_async(
                schoolframespath + item.name, 
                modelpath + 'frames/' + newname, 
                school_x_max, 
                school_y_max, 
                crypt=do_crypt
              )
              t = trainframe(
                made=item.time,
                school=params['school'],
                name=newname,
                code='NE',
                checked=0,
                made_by_id=self.user.id,
              )
              t.encrypted = False
              t.c0=params['cblist'][i][0]
              t.c1=params['cblist'][i][1] 
              t.c2=params['cblist'][i][2]
              t.c3=params['cblist'][i][3]
              t.c4=params['cblist'][i][4]
              t.c5=params['cblist'][i][5]
              t.c6=params['cblist'][i][6]
              t.c7=params['cblist'][i][7]
              t.c8=params['cblist'][i][8]
              t.c9=params['cblist'][i][9]
              await t.asave()
              trainers_redis.set_last_frame(params['school'], t.id)
              item.trainframe = t.id
              await item.asave(update_fields=('trainframe', ))
            i += 1 
          eventline.done = True  
          await eventline.asave(update_fields=('done', ))

        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))		

      elif params['command'] == 'delevent':
        try:
          if params['eventnr'] == -1:
            eventlines = event.objects.filter(camera__id=params['streamnr'], xmax__gt=0)
          elif params['eventnr'] == 0:
            eventlines = event.objects.filter(camera__id=params['streamnr'], xmax__gt=0, 
              done=True)
          else:
            eventlines = event.objects.filter(id=params['eventnr'])
          streamnr =  params['streamnr']
          if await access.check_async('C', streamnr, self.scope['user'], 'W'):
            async for eventline in eventlines:
              eventline.deleted = True
              await eventline.asave(update_fields = ['deleted'])
        except event.DoesNotExist:
          logger.warning('delevent - Did not find DB line: ' + str(params['eventnr']))
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))			

      elif params['command'] == 'delitem':
        if params['dtype'] == 0:
          frameline = await event_frame.objects.aget(id=params['nr_todel'])
          eventline = await event.objects.aget(id=params['event_nr'])
          streamline = await stream.objects.aget(event__id=eventline.id)
          if await access.check_async('C', streamline.id, self.scope['user'], 'W'):
            frameline.deleted = True
            await frameline.asave(update_fields=('deleted', ))
        elif params['dtype'] == 1:
          eventline = await event.objects.aget(id=params['nr_todel'])
          streamline = await stream.objects.aget(event__id=eventline.id)
          if await access.check_async('C', streamline.id, self.scope['user'], 'W'):
            if await event.objects.filter(videoclip=eventline.videoclip).acount() <= 1:
              videofile = recordingspath + eventline.videoclip
              if await aiofiles.os.path.exists(videofile + '.mp4'):
                await aiofiles.os.remove(videofile + '.mp4')
              else:
                logger.warning('delitem - Delete did not find: ' + videofile + '.mp4')
              if await aiofiles.os.path.exists(videofile + '.webm'):
                await aiofiles.os.remove(videofile + '.webm')
              else:
                logger.warning('delitem - Delete did not find: ' + videofile + '.webm')
              if await aiofiles.os.path.exists(videofile + '.jpg'):
                await aiofiles.os.remove(videofile + '.jpg')
              else:
                logger.warning('delitem - Delete did not find: ' + videofile + '.jpg')
            eventline.videoclip = ''
            await eventline.asave(update_fields=('videoclip', ))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))		

      elif params['command'] == 'remfrschool':
        eventline = await event.objects.aget(id=params['event'])
        streamline = await stream.objects.aget(event__id=eventline.id)
        if await access.check_async('C', streamline.id, self.scope['user'], 'W'):
          eventline.done = True
          await eventline.asave(update_fields=('done', ))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))			

      elif params['command'] == 'setonetag':
        frameline = await trainframe.objects.aget(id=params['img'],)
        schoolline = await school.objects.aget(id=params['school'],)
        if access.check('S', schoolline.id, self.scope['user'], 'W'):
          fieldtochange = 'c'+params['cnt']
          setattr(frameline, fieldtochange, params['value'])
          await frameline.asave(update_fields=(fieldtochange, ))
          outlist['data'] = 'OK'
          logger.debug('--> ' + str(outlist))
          await self.send(json.dumps(outlist))		

      elif params['command'] == 'importimages':
        schoolline = await school.objects.aget(id=params['school'])
        modelpath = schoolline.dir
        if await access.check_async('S', params['school'], self.scope['user'], 'W'):
          for item in glob('temp/unpack/' + params['filesdir'] + '/*'):
            pathadd = str(randint(0,99))+'/'
            await aiofiles.os.makedirs(modelpath + 'frames/' + pathadd, exist_ok=True)
            filename = item.split('/')[-1]
            newname = await uniquename_async(modelpath + 'frames/', 
                pathadd + filename, 'bmp')
            await reduce_image_async(
              item, 
              modelpath + 'frames/' + newname, 
              school_x_max, 
              school_y_max, 
            )
            t = trainframe(
              made=timezone.make_aware(datetime.now()),
              school=params['school'],
              name=newname,
              code='NE',
              checked=0,
              made_by_id=self.user.id,
            )
            t.encrypted = False
            for i in range(10):
              tagname = 'c'+str(i)
              if params['tag'] == i:
                setattr(t, tagname, 1)
              else:
                setattr(t, tagname, 0)  
            await t.asave()
          await aioshutil.rmtree('temp/unpack/' + params['filesdir'])
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
     
    except asyncio.CancelledError:
      # Client went away. That is normal
      return()
        
    except:
      logger.error('Error in consumer: ' + logname + ' (schooldbutil)')
      logger.error(format_exc())

#*****************************************************************************
# SchoolUtil
#*****************************************************************************

class schoolutil(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      self.ws_session = None
      self.authed = False
      await self.accept()
    except:
      logger.error('Error in consumer: ' + logname + ' (schooldbutil)')
      logger.error(format_exc())

  async def disconnect(self, code):
    try:
      if self.ws_session is not None:
        await self.ws_session.close()
      close_old_connections()    
    except:
      logger.error('Error in consumer: ' + logname + ' (trainerutil)')
      logger.error(format_exc())

  async def receive(self, text_data):
    try:
      #logger.info('<-- ' + text_data)
      params = json.loads(text_data)['data']
      outlist = {'tracker' : json.loads(text_data)['tracker']}	

      if params['command'] == 'delschool':
        if not self.authed:
          self.schoolline = await school.objects.aget(id=params['schoolnr'])
          t_query = self.schoolline.trainers.filter(active = True)
          trainerline = await t_query.afirst()
          self.user = self.scope['user']
          if not self.user.is_authenticated:
            self.user = await dbuser.objects.aget(username=params['name'])
            if self.user.check_password(params['pass']):
              logger.info('Successfull login:' + params['name'] + ' - Software v' 
                + await agetconfig('version', '?'))
              self.authed = True
            if not self.authed:
              logger.info('Login failure: ' + params['name'])
              await self.close() 
        if await access.check_async('S', params['schoolnr'], self.user, 'W'):
          if (count := await stream.objects.filter(
              active=True, 
              eve_school=self.schoolline).acount()
            ):
            outlist['data'] = {
              'status' : 'streams_linked', 
              'count' : count, 
              'domain' : myserver,
            }
          else:  
            if trainerline.t_type in {2, 3}:
              from aiohttp import ClientSession
              async with ClientSession() as session:
                async with session.ws_connect(trainerline.wsserver + 'ws/schoolutil/') as ws:
                  temp = json.loads(text_data)
                  temp['data']['schoolnr']=self.schoolline.e_school
                  temp['data']['name']=trainerline.wsname
                  temp['data']['pass']=trainerline.wspass
                  await ws.send_str(json.dumps(temp))
                  returned = await ws.receive() 
              outlist['data'] = json.loads(returned.data)['data']    
            else:
              if await aiofiles.os.path.exists(self.schoolline.dir):
                await aioshutil.rmtree(self.schoolline.dir)
              else:
                logger.warning('***** Dir ' + self.schoolline.dir + ' not found')
              outlist['data'] = {'status' : 'OK', }
            if outlist['data']['status'] == 'OK': 
              self.schoolline.active = False
              await self.schoolline.asave(update_fields=('active', ))
              await access_control.objects.filter(
                vtype = 'S', 
                vid = params['schoolnr'], 
              ).adelete()
        else:  
          outlist['data'] = {
            'status' : 'no_priv', 
            'domain' : myserver,
          }
        #logger.info('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
      
    except:
      logger.error('Error in consumer: ' + logname + ' (schooldbutil)')
      logger.error(format_exc())
