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

V1.6.6 31.03.2025
"""

import cv2 as cv
import json
import numpy as np
import asyncio
import aiofiles
import aiofiles.os
import aioshutil
from aiopath import AsyncPath
from logging import getLogger
from signal import SIGKILL
from os import environ, kill, getpid
from traceback import format_exc
from setproctitle import setproctitle
from collections import deque
from time import time
from threading import Lock as t_lock
from multiprocessing import Process
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.forms.models import model_to_dict
from tools.l_break import a_break_type, break_type, a_break_time, BR_MEDIUM, BR_LONG
from tools.c_spawn import viewable
from tools.c_tools import (
  add_record_count, 
  take_record_count, 
  add_data_count, 
  take_data_count, 
)
from tf_workers.models import school
from startup.redis import my_redis as startup_redis
from schools.c_schools import get_taglist
from streams.redis import my_redis as streams_redis
from users.userinfo import afree_quota
from .c_alarm import alarm, alarm_init

class c_eventer(viewable):
  def __init__(self, dbline, worker_inqueue, worker_registerqueue, worker_id, logger, ):
    from l_buffer.l_buffer import l_buffer
    from tools.c_tools import c_buffer
    self.type = 'E'
    self.dbline = dbline
    self.id = dbline.id
    if self.dbline.cam_virtual_fps:
      self.dataqueue = c_buffer()
    else:  
      self.dataqueue = c_buffer(
        block_put = False, 
        #debug = 'Eve' + str(self.id), 
      )
    self.detectorqueue = l_buffer(
      'ONOOB', 
      #debug = '?????' + self.type + str(self.id),
    )
    self.worker_in = worker_inqueue
    self.worker_reg = worker_registerqueue
    self.tf_worker_id = worker_id
    self.cond_dict = {1:[], 2:[], 3:[], 4:[], 5:[]}
    super().__init__(logger, )
    
  async def process_received(self, received):  
    result = True
    #print('*** Eventer-Inqueue received:', received)
    if (received[0] == 'new_video'):
      with self.vid_deque_lock:
        self.vid_deque.append(received[1:])
        while True:
          if self.vid_deque and (time() - self.vid_deque[0][2]) > 180.0:
            listitem = self.vid_deque.popleft()
            try:
              await aiofiles.os.remove(self.recordingspath + listitem[1])
            except FileNotFoundError:
              self.logger.warning('c_eventers.py:new_video - Delete did not find: '
                + self.recordingspath + listitem[1])# Liste der zu löschenden Schlüssel
            keys_to_delete = [item 
              for item in self.vid_str_dict 
              if item == str(listitem[0]) or item.endswith('_' + str(listitem[0]))]
            for key in keys_to_delete:
                del self.vid_str_dict[key]
          else:
            break
    elif (received[0] == 'purge_videos'):
      with self.vid_deque_lock:
        for item in self.vid_deque.copy():
          try:
            await aiofiles.os.remove(self.recordingspath + item[1])
          except FileNotFoundError:
            self.logger.warning('c_eventers.py:purge_videos - Delete did not find: '
              + self.recordingspath + item[1])
        self.vid_deque.clear()
    elif (received[0] == 'set_fpslimit'):
      self.dbline.eve_fpslimit = received[1]
      if received[1] == 0:
        self.sl.period = 0.0
      else:
        self.sl.period = 1.0 / received[1]
    elif (received[0] == 'set_margin'):
      self.dbline.eve_margin = received[1]
    elif (received[0] == 'set_event_time_gap'):
      self.dbline.eve_event_time_gap = received[1]
    elif (received[0] == 'set_school'):
      self.school_line = await school.objects.aget(id=received[1])
      self.dbline.eve_school = self.school_line
    elif (received[0] == 'set_alarm_email'):
      self.dbline.eve_alarm_email = received[1]
    elif (received[0] == 'cond_open'):
      self.nr_of_cond_ed += 1
      self.last_cond_ed = received[1]
    elif (received[0] == 'cond_close'):
      self.nr_of_cond_ed = max(0, self.nr_of_cond_ed - 1)
    elif (received[0] == 'new_condition'):
      self.cond_dict[received[1]].append(received[2])
      self.set_cam_counts()
    elif (received[0] == 'del_condition'):
      self.cond_dict[received[1]] = [item 
        for item in self.cond_dict[received[1]] 
        if item['id'] != received[2]]
      self.set_cam_counts()
    elif (received[0] == 'save_condition'):
      for item in self.cond_dict[received[1]]:
        if item['id'] == received[2]:
          item['c_type'] = received[3]
          item['x'] = received[4]
          item['y'] = received[5]
          break
      self.set_cam_counts()
    elif (received[0] == 'save_conditions'):
      self.cond_dict[received[1]] = json.loads(received[2])
      self.set_cam_counts()
    elif (received[0] == 'setdscrwidth'):
      self.scrwidth = received[1]
      self.scaling = None
    elif (received[0] == 'reset'):
      await self.dbline.arefresh_from_db()
    else:
      result = False  
    return(result)
 
  async def async_runner(self):
    import django
    django.setup()
    from l_buffer.l_buffer import l_buffer
    from globals.c_globals import tf_workers
    from tools.l_tools import djconf
    from tools.c_tools import hasoverlap, rect_btoa
    self.hasoverlap = hasoverlap
    self.rect_btoa = rect_btoa
    from tools.c_logger import alog_ini
    from schools.c_schools import get_taglist
    from streams.models import stream
    from tf_workers.c_tf_workers import tf_worker_client
    from .c_event import resolve_rules
    self.resolve_rules = resolve_rules
    self.stream = stream
    try: 
      self.logname = 'eventer #'+str(self.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Eventer #' + str(self.id))
      await super().async_runner()  
      self.vid_deque_lock = None
      self.display_ts = 0
      self.nr_of_cond_ed = 0
      await self.read_conditions()
      eve_school = await database_sync_to_async(lambda: self.dbline.eve_school)() 
      self.tag_list_active = eve_school.id
      self.tag_list = await asyncio.to_thread(get_taglist, self.tag_list_active)
      datapath = await djconf.agetconfig('datapath', 'data/')
      self.recordingspath = await djconf.agetconfig(
        'recordingspath', datapath + 'recordings/', 
      )
      
      await database_sync_to_async(alarm_init)(self.logger, self.id)
      environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
      if self.dbline.eve_gpu_nr_cv== -1:
        environ["CUDA_VISIBLE_DEVICES"] = ''
      else:  
        environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.eve_gpu_nr_cv)
      self.logger.info('**** Eventer #' + str(self.id)+' running GPU #' 
        + str(self.dbline.eve_gpu_nr_cv))
      self.eventdict = {}
      self.eventdict_lock = t_lock()
      self.display_lock = t_lock()
      self.vid_deque = deque()
      self.vid_deque_lock = t_lock()
      self.vid_str_dict = {}
      self.set_cam_counts()
      self.display_deque = deque()
      self.tf_worker = tf_worker_client(self.worker_in, self.worker_reg, )
      self.tf_w_index = await self.tf_worker.register(self.tf_worker_id)
      await self.tf_worker.run_out(self.tf_w_index)
      self.school_line = await database_sync_to_async(lambda: self.dbline.eve_school)()
      self.xdim, self.ydim = await self.tf_worker.get_xy(
        self.school_line.id,
        self.tf_w_index
      )
      self.finished = False
      self.scaling = None
      self.scrwidth = None 
      self.motion_frame = [0,0,0.0]
      self.last_insert_ts = float('inf')
      self.run_one_task = None
      asyncio.create_task(self.check_events())
      asyncio.create_task(self.tags_refresh())
      asyncio.create_task(self.inserter())
      if self.dbline.eve_webm_doit:
        asyncio.create_task(self.make_webm())
      #print('Launch: eventer')
      while self.do_run:
        if streams_redis.check_if_counts_zero('E', self.id):
          await a_break_type(BR_LONG)
        frameline = await self.dataqueue.get()
        if not self.do_run:
          break  
        if (frameline is not None and frameline[0] is not None 
            and self.sl.greenlight(frameline[2])):
          if self.run_one_task is None or self.run_one_task.done():  
            self.run_one_task = asyncio.create_task(self.run_one(frameline))
        else:
          await a_break_type(BR_MEDIUM)
      self.dataqueue.stop()
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
      self.tf_worker.stop_out(self.tf_w_index)
      await self.tf_worker.unregister(self.tf_w_index)
      #for thread in enumerate(): 
      #  print(thread)
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())
      self.logger.info('Restarting process...')
      while True:
        await a_break_type(BR_LONG)
        if not startup_redis.get_start_stream_busy(): 
          break
      startup_redis.set_start_stream_busy(self.id)
      kill(getpid(), SIGKILL)

  async def run_one(self, frame):
    if streams_redis.check_if_counts_zero('E', self.id):
      await a_break_type(BR_LONG)
      return()
    #await a_break_type(BR_LONG)
    print('33333')
    if streams_redis.view_from_dev('E', self.id):
      while self.scrwidth is None:
        await a_break_type(BR_LONG)
      if self.do_run and frame[0]:
        if self.scaling is None:
          if frame[1].shape[1] > self.scrwidth:
            self.scaling = self.scrwidth / frame[1].shape[1]
          else:
            self.scaling = 1.0  
          self.linewidth = round(4.0 / self.scaling)
          self.textheight = round(0.51 / self.scaling)
          self.textthickness = round(2.0 / self.scaling)
        await self.display_events(frame)
    if self.do_run and self.dbline.eve_view:
      fps = self.som.gettime()
      if fps:
        self.dbline.eve_fpsactual = fps
        await database_sync_to_async(
          self.stream.objects.filter(id=self.id).update
        )(eve_fpsactual = fps)
        streams_redis.fps_to_dev('E', self.id, fps)

  async def read_conditions(self):
    from .models import evt_condition
    self.cond_dict = {1:[], 2:[], 3:[], 4:[], 5:[]}
    condition_lines = evt_condition.objects.filter(eventer_id=self.id)
    async for item in condition_lines:
      self.cond_dict[item.reaction].append(model_to_dict(item))

  def merge_events(self):
    while True:
      del_set = set()
      with self.eventdict_lock:
        i_list = list(self.eventdict.items())
      j_list = i_list
      for i, event_i in i_list:
        if not event_i.check_out_ts:
          for j, event_j in j_list:
            if j > i:
              if not event_j.check_out_ts:
                if self.hasoverlap(event_i, event_j):
                  event_i[0] = min(event_i[0], event_j[0])
                  event_i[1] = max(event_i[1], event_j[1])
                  event_i[2] = min(event_i[2], event_j[2])
                  event_i[3] = max(event_i[3], event_j[3])
                  event_i.start = min(event_i.start, event_j.start)
                  event_i.end = max(event_i.end, event_j.end)
                  event_i.merge_frames(event_j)
                  del_set.add(j) 
      if del_set:   
        with self.eventdict_lock:
          for j in del_set:
            if j in self.eventdict:
              del self.eventdict[j]
      else:
        break

  async def display_events(self, frame):
    self.display_deque.append(frame) 
    with self.display_lock:
      display_list = [
        item for item in self.eventdict.values() if item.check_out_ts is None
      ]
    if (display_list 
        and self.display_deque[0][2] > self.last_insert_ts + self.dbline.eve_sync_factor):
      return()
    newframe = self.display_deque.popleft()
    newframe[1] = newframe[1].copy()  # Ensure the array is writable
    for item in display_list:
      predictions = item.pred_read(max=1.0)
      if self.resolve_rules(self.cond_dict[1], predictions):
        if self.nr_of_cond_ed <= 0:
          self.last_cond_ed = 1
        if self.resolve_rules(self.cond_dict[self.last_cond_ed], predictions):
          colorcode= (0, 0, 255)
        else:
          colorcode= (0, 255, 0)
        tag_display_list = [(j, predictions[j]) for j in range(1, len(self.tag_list)) 
          if predictions[j] >= 0.5]
        tag_display_list.sort(key = lambda x: -x[1])
        tag_display_list = tag_display_list[:3]
        cv.rectangle(newframe[1], self.rect_btoa(item[:4]), colorcode, self.linewidth)
        if item[2] < (self.dbline.cam_yres - item[3]):
          y0 = item[3] + 30 * self.textheight
        else:
          y0 = item[2] - (10 + (len(tag_display_list) - 1) * 30) * self.textheight
        for j in range(len(tag_display_list)):
          cv.putText(newframe[1], 
            self.tag_list[tag_display_list[j][0]].name[:3]
            +' - '+str(round(tag_display_list[j][1],2)), 
            (item[0]+2, y0 + j * 30 * self.textheight), 
            cv.FONT_HERSHEY_SIMPLEX, self.textheight, colorcode, 
            self.textthickness, cv.LINE_AA)
    await self.viewer.inqueue.put(newframe)
    del newframe  

  async def make_webm(self):
    while self.do_run:
      path = AsyncPath(self.recordingspath)
      async for mp4_file in path.glob('E_????????????.mp4'):
        mp4_file = str(mp4_file)
        webm_file = mp4_file[:-4] + '.webm'
        if not await aiofiles.os.path.exists(webm_file):
          if self.dbline.eve_webm_procnum_limit:
            descriptor = ['taskset', '-c', '0', ]
          else:
            descriptor = [] 
          descriptor += ['ffmpeg', ]
          descriptor += ['-v', 'fatal', ]
          if self.dbline.eve_webm_fps:
            descriptor += ['-r', str(self.dbline.eve_webm_fps), ]
          if self.dbline.eve_webm_threads:
            descriptor += ['-threads', str(self.dbline.eve_webm_threads), ]
          descriptor += ['-i', mp4_file, ]
          if self.dbline.eve_webm_crf:
            descriptor += ['-crf', str(self.dbline.eve_webm_crf), ]
          if self.dbline.eve_webm_width:
            descriptor += ['-vf', 'scale=' + str(self.dbline.eve_webm_width)+':-1', ]
          descriptor += [webm_file, ]
          #print(descriptor)
          process = await asyncio.create_subprocess_exec(*descriptor)
          await process.wait()
      await a_break_time(10.0)
    
  async def check_event(self, i, item):
    if self.dbline.cam_virtual_fps:
      newtime = streams_redis.get_virt_time(self.id)
    else:
      newtime = time()  
    if (item.end < newtime - self.dbline.eve_event_time_gap 
        or item.end > item.start + 20.0):
        #or item.end > item.start + 120.0):
      item.check_out_ts = item.end
    if self.cond_dict[5]:
      predictions = item.pred_read(max=1.0)
    else:
      predictions = None   
    if self.resolve_rules(self.cond_dict[5], predictions):
      await alarm(self.id, predictions) 
    if item.check_out_ts:
      if predictions is None and self.cond_dict[2]:
        predictions = item.pred_read(max=1.0)
      item.goes_to_school = self.resolve_rules(self.cond_dict[2], predictions)
      if predictions is None and self.cond_dict[3]:
        predictions = item.pred_read(max=1.0)
      item.isrecording = self.resolve_rules(self.cond_dict[3], predictions)
      if predictions is None and self.cond_dict[4]:
        predictions = item.pred_read(max=1.0)
      if self.resolve_rules(self.cond_dict[4], predictions):
        item.to_email = self.dbline.eve_alarm_email
      else:
        item.to_email = ''
      is_ready = True
      if item.goes_to_school or item.isrecording or item.to_email:
        if await afree_quota(item.stream_creator):
          if item.isrecording:
            with self.vid_deque_lock:
              if (checkbool := (self.vid_deque 
                  and item.check_out_ts <= self.vid_deque[-1][2])):
                my_vid_list = [v_item for v_item in self.vid_deque 
                  if item.start <= v_item[2] and item.end >= v_item[2] - 10.5]   
                #10 seconds video length plus average trigger delay from checkmp4
                #print(my_vid_list)
                my_vid_start = my_vid_list[0][2]
            if checkbool:
              vid_offset = item.focus_time - my_vid_start
              vid_offset = max(vid_offset, 0.0)
              my_vid_str = '_'.join([str(sublist[0]) for sublist in my_vid_list])
              if my_vid_str in self.vid_str_dict:
                item.savename=self.vid_str_dict[my_vid_str]
                isdouble = True
              else:
                await item.dbline.asave()
                item.savename = ('E_'
                  +str(item.dbline.id).zfill(12)+'.mp4')
                savepath = (self.recordingspath + item.savename)
                temppath = (self.recordingspath + 'temp_' + item.savename)
                if len(my_vid_list) == 1: 
                  await aioshutil.copyfile(
                    self.recordingspath + my_vid_list[0][1], 
                    savepath
                  )
                else:
                  listfilename = (self.recordingspath + 'T_'
                    + str(item.dbline.id).zfill(12)+'.temp')
                  listfilename = await aiofiles.os.path.abspath(listfilename)
                  savepath = await aiofiles.os.path.abspath(savepath)
                  async with aiofiles.open(listfilename, 'w') as f1:
                    for line in my_vid_list:
                      await f1.write(
                        'file ' 
                        + await aiofiles.os.path.abspath(self.recordingspath + line[1]) 
                        + '\n'
                      )
                  process = await asyncio.create_subprocess_exec(
                    'ffmpeg', 
                    '-f', 'concat', 
                    '-safe', '0', 
                    '-v', 'fatal', 
                    '-i', listfilename, 
                    '-codec', 'copy', 
                    temppath,
                  )
                  await process.wait()
                  await aiofiles.os.remove(listfilename)
                  await aioshutil.move(temppath, savepath)
                self.vid_str_dict[my_vid_str] = item.savename
                isdouble = False
              item.dbline.videoclip = item.savename[:-4]
              item.dbline.double = isdouble
              await item.dbline.asave()
              if not isdouble:
                await asyncio.create_subprocess_exec(
                  'ffmpeg', 
                  '-ss', str(vid_offset), 
                  '-v', 'fatal', 
                  '-i', savepath, 
                  '-vframes', '1', 
                  '-q:v', '2', 
                  savepath[:-4]+'.jpg'
                )
            else:  
              is_ready = False
          if is_ready:
            await item.save(self.cond_dict)
        else:
          self.logger.warning('!!!!! Did not save the event because of low quota')    
      if is_ready: 
        with self.eventdict_lock:
          with self.display_lock:
            if i in self.eventdict:
              del self.eventdict[i]

  async def check_events(self):
    try:
      while self.do_run:
        await(a_break_type(BR_LONG))
        for i in list(self.eventdict.keys()):
          try:
            item = self.eventdict[i]
            await(self.check_event(i, item))
          except KeyError:
            pass 
    except:
      self.logger.error('Error in process: ' + self.logname + ' (check_events)')
      self.logger.error(format_exc())

  async def tags_refresh(self):
    try:
      while self.do_run:
        await(a_break_time(60.0))
        await database_sync_to_async(self.school_line.refresh_from_db)()
        if self.tag_list_active != self.dbline.eve_school.id:
          self.tag_list_active = self.dbline.eve_school.id
          self.taglist = await database_sync_to_async(get_taglist)(self.tag_list_active) 
    except:
      self.logger.error('Error in process: ' + self.logname + ' (tags_refresh)')
      self.logger.error(format_exc())
      
  async def inserter(self):
    from .c_event import c_event
    try:
      while (not (await self.tf_worker.check_ready(self.tf_w_index))):
        await a_break_type(BR_LONG)
      detector_buffer = deque()
      while self.do_run:
        while True:
          frame = await self.detectorqueue.get()
          if frame == 'stop':
            break
          else:
            detector_buffer.append(frame)
        if detector_buffer:
          imglist = [
            cv.cvtColor(frame[1], cv.COLOR_BGR2RGB) for frame in detector_buffer
          ]
          del frame
          ts = time()
          if not await self.tf_worker.ask_pred(
            self.school_line.id, 
            imglist, 
            self.tf_w_index,
          ):
            await a_break_type(BR_MEDIUM)
            continue
          ts = time()
          predictions = []
          for frame in detector_buffer:
            if len(predictions) == 0:
              predictions = await self.tf_worker.get_from_outqueue(self.tf_w_index)
            prediction = predictions[0]
            predictions = predictions[1:]
            frame = frame + [prediction]
            found = None
            margin = self.dbline.eve_margin
            for j, item in list(self.eventdict.items()):
              if self.hasoverlap((frame[3][0] - margin, frame[3][1] + margin, 
                  frame[3][2] - margin, frame[3][3] + margin), item):
                found = item
                break
            if found is None or found.check_out_ts:
              count = 0  
              while count in self.eventdict:
                count += 1   
              new_event = await c_event.create(self.tf_worker, self.tf_w_index, frame, 
                margin, self.dbline, self.school_line.id, count, self.logger)
              with self.eventdict_lock:
                self.eventdict[count] = new_event
            else: 
              found.add_frame(frame)
          self.merge_events()
          self.last_insert_ts = frame[2]
          del frame
          detector_buffer.clear()
      return()  
    except:
      self.logger.error('Error in process: ' + self.logname + ' (inserter)')
      self.logger.error(format_exc())
      self.logger.info('Restarting process...')
      while startup_redis.get_start_stream_busy(): 
        await a_break_type(BR_LONG)
      startup_redis.set_start_stream_busy(self.id)
      kill(getpid(), SIGKILL)

  def set_cam_counts(self):
    if any([len(self.cond_dict[x]) for x in range(2,6)]):
      add_data_count(self.type, self.id) #just switch 0 or 1
    else:
      take_data_count(self.type, self.id)
    if self.cond_dict[3]:
      add_record_count(self.type, self.id)
    else:
      take_record_count(self.type, self.id)

  def build_string(self, i):
    if i['c_type'] == 1:
	    result = 'Any movement detected'
    elif  i['c_type'] in {2, 3}:
	    result = str(i['x'])+' predictions are '
    elif i['c_type']  in {4, 5}:
	    result = 'Tag "'+self.tag_list[i['x']].name+'" is '
    elif i['c_type'] == 6:
	    result = ('Tag "'+self.tag_list[i['x']].name+'" is in top '
        +str(round(i['y'])))
    if i['c_type'] in {2,4}:
	    result += 'above or equal '+str(i['y'])
    elif i['c_type'] in {3,5}:
	    result += 'below or equal '+str(i['y'])
    return(result)   
      
  def reset(self):  
    self.inqueue.put(('reset', ))

  def stop(self):
    self.dataqueue.stop()
    super().stop()
    
