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

import os
import cv2 as cv
import json
import numpy as np
import asyncio
import aiofiles
import aiofiles.os
import aioshutil
import signal
from logging import getLogger
from signal import SIGKILL
from setproctitle import setproctitle
from collections import deque
from time import time
from multiprocessing import Process as mp_process, SimpleQueue as s_queue
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from django.forms.models import model_to_dict
from globals.c_globals import add_viewer
from tools.l_break import (
  a_break_type, 
  break_type, 
  a_break_time, 
  BR_SHORT, 
  BR_MEDIUM, 
  BR_LONG,
)
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
from oneitem.shared_mem import shared_mem
from l_buffer.l_buffer import l_buffer
from viewers.c_viewers import c_viewer
from tools.l_tools import djconf
from tools.c_tools import c_buffer, speedlimit, speedometer, hasoverlap, rect_btoa
from tools.c_logger import alog_ini
from streams.models import stream
from tf_workers.c_tf_workers import tf_worker_client
from .models import evt_condition
from .redis import my_redis as eventers_redis
from .c_alarm import alarm, alarm_init
from .c_event import resolve_rules, c_event

MAX_EVENT_LENGTH = 120

_SH_MEM_ITEMS = {
    'fps_limit' : 'd',
    'margin' : 'i',
    'event_time_gap' : 'i',
    'shrink_factor' : 'd',
    'sync_factor' : 'd',
    'school' : 'i',
    'alarm_max_nr' : 'i',
    'one_frame_per_event' : 'i',
    'nr_of_cond_ed' : 'i',
    'last_cond_ed' : 'i',
    'x_canvas' : 'i',
    'aoi_xdim' : 'i',
    'aoi_ydim' : 'i',
}

class c_eventer():
  def __init__(self, dbline, my_worker, logger, ):
    self.type = 'E'
    self.dbline = dbline
    self.id = dbline.id
    add_viewer((my_viewer := c_viewer(
      self.type, 
      self.id, 
      logger,
    )))
    self.viewer = my_viewer
    streams_redis.zero_to_dev(self.type, self.id)
    streams_redis.fps_to_dev(self.type, self.id, 0.0)
    self.shared_mem = shared_mem(
      source_dict = _SH_MEM_ITEMS, 
    )
    self.shared_mem.write_1_meta('fps_limit', dbline.eve_fpslimit)
    self.shared_mem.write_1_meta('margin', dbline.eve_margin)
    self.shared_mem.write_1_meta('event_time_gap', dbline.eve_event_time_gap)
    self.shared_mem.write_1_meta('shrink_factor', dbline.eve_shrink_factor)
    self.shared_mem.write_1_meta('sync_factor', dbline.eve_sync_factor)
    self.shared_mem.write_1_meta('school', dbline.eve_school.id)
    self.shared_mem.write_1_meta('alarm_max_nr', dbline.eve_alarm_max_nr)
    self.shared_mem.write_1_meta('one_frame_per_event', dbline.eve_one_frame_per_event)
    self.shared_mem.write_1_meta('nr_of_cond_ed', 0)
    self.eve_worker = eve_worker(
      dbline, 
      my_viewer.inqueue,
      my_worker.inqueue,
      my_worker.registerqueue,
      my_worker.id,
      logger, 
      self.shared_mem.shm.name, 
    ) 

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
    
  def start(self):
    self.eve_worker.start()
    self.viewer.inqueue.display_qinfo(info = self.type + ' ' + str(self.id) +  ' Spawn: ')
    self.viewer.inqueue.start_data_loop()
  
  async def stop(self):
    if self.eve_worker.is_alive():
      await asyncio.to_thread(self.eve_worker.inqueue.put, ('stop',))
      try:
        await asyncio.to_thread(self.eve_worker.join, 5.0)
      except RuntimeError:
        pass  # executor already shutting down
    self.shared_mem.shm.close() 
    self.shared_mem.shm.unlink()
    
class eve_worker(mp_process):
  def __init__(self, 
      dbline, 
      myviewer_queue, 
      worker_inqueue, 
      worker_registerqueue, 
      worker_id,
      logger, 
      shm_name, 
    ):
    super().__init__()
    self.type = 'E'
    self.id = dbline.id
    self.dbline = dbline
    if self.dbline.cam_virtual_fps:
      self.dataqueue = c_buffer(
        #debug = 'Eve' + str(self.id), 
      )
    else:  
      self.dataqueue = c_buffer(
        block_put = False, 
        #debug = 'Eve' + str(self.id), 
      )
    self.detectorqueue = l_buffer(
      'ONOOB', 
      #debug = '?????' + self.type + str(self.id),
    )
    self.viewer_queue = myviewer_queue
    self.worker_in = worker_inqueue
    self.worker_reg = worker_registerqueue
    self.tf_worker_id = worker_id
    self.cond_dict = {1:[], 2:[], 3:[], 4:[], 5:[]}
    self.last_saved_event_end = 0.0
    self.inqueue = s_queue()
    self.shm_name = shm_name

  def run(self):
    asyncio.run(self.async_runner()) 
    
  def sigint_handler(self, signal = None, frame = None ):
    self.got_sigint = True 

  async def in_queue_thread(self):
  # Needs to be cleaned up. Not everything is used anymore
    try:
      while self.do_run:
        received = await asyncio.to_thread(self.inqueue.get)
        #print(f'***** EVE Inqueue #{self.id}:', received) 
        if (received[0] == 'new_video'):
          async with self.vid_deque_lock:
            self.vid_deque.append(received[1:])
            while True:
              if (self.vid_deque 
                  and (self.last_saved_event_end - self.vid_deque[0][2]) > 240.0):
                listitem = self.vid_deque.popleft()
                try:
                  await aiofiles.os.remove(self.recordingspath + listitem[1])
                  await a_break_type(BR_SHORT)
                except FileNotFoundError:
                  self.logger.warning('c_eventers.py:new_video - Delete did not find: '
                    + self.recordingspath + listitem[1])# Liste der zu löschenden Schlüssel
                keys_to_delete = [item 
                  for item in self.vid_str_dict 
                  if item == str(listitem[0]) or item.endswith('_' + str(listitem[0]))]
                for key in keys_to_delete:
                    del self.vid_str_dict[key]
              else:
                await a_break_type(BR_SHORT)
                break
        elif (received[0] == 'purge_videos'):
          async with self.vid_deque_lock:
            for item in self.vid_deque.copy():
              try:
                await aiofiles.os.remove(self.recordingspath + item[1])
                await a_break_type(BR_SHORT)
              except FileNotFoundError:
                self.logger.warning('c_eventers.py:purge_videos - Delete did not find: '
                  + self.recordingspath + item[1])
            self.vid_deque.clear()
        elif (received[0] == 'set_alarm_email'):
          self.email_address = received[1]
        elif (received[0] == 'new_condition'):
          self.cond_dict[received[1]].append(received[2])
          await self.set_cam_counts()
        elif (received[0] == 'save_conditions'):
          self.cond_dict[received[1]] = json.loads(received[2])
          await self.set_cam_counts()
        elif (received[0] == 'stop'):
          self.got_sigint = True
          self.do_run = False  
          if self.is_alive():
            if self._inq_task:
              self._inq_task.cancel()
              try:
                await self._inq_task
              except asyncio.CancelledError:
                pass
        else:
          self.logger.warning( 
              f'CA{self.id}: Unknown key in Inqueue: {received[0]}'
          )
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("in_queue_thread crashed: %s", fatal, exc_info=True) 
    
  async def async_runner(self):
    try:
      self.logname = 'eventer #'+str(self.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Eventer #' + str(self.id))
      self.dbline = await stream.objects.aget(id = self.id)
      self.shared_mem = shared_mem(
        source_dict = _SH_MEM_ITEMS, 
        shm_name=self.shm_name, 
      )
      self.got_sigint = False
      self._inq_task = None
      self.sl = speedlimit(period = 0.0)
      self.som = speedometer()
      self.do_run = True
      loop = asyncio.get_running_loop()
      loop.add_signal_handler(signal.SIGINT, self.sigint_handler)
      self._inq_task = asyncio.create_task(
        self.in_queue_thread(), 
        name = 'in_queue_thread', 
      )
      self.display_ts = 0
      self.cond_dict = {1:[], 2:[], 3:[], 4:[], 5:[]}
      condition_lines = evt_condition.objects.filter(eventer_id=self.id)
      async for item in condition_lines:
        self.cond_dict[item.reaction].append(model_to_dict(item)) 
      self.tag_list_active = self.shared_mem.read_1_meta('school')
      self.tag_list = await asyncio.to_thread(get_taglist, self.tag_list_active)
      datapath = await djconf.agetconfig('datapath', 'data/')
      self.recordingspath = await djconf.agetconfig(
        'recordingspath', datapath + 'recordings/', 
      )
      await database_sync_to_async(alarm_init)(self.logger) 
      os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
      if self.dbline.eve_gpu_nr_cv== -1:
        os.environ["CUDA_VISIBLE_DEVICES"] = ''
      else:  
        os.environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.eve_gpu_nr_cv)
      self.logger.info('**** Eventer #' + str(self.id)+' running GPU #' 
        + str(self.dbline.eve_gpu_nr_cv))
      self.event_dict = {}
      self.event_dict_lock = asyncio.Lock()
      self.vid_deque = deque()
      self.vid_deque_lock = asyncio.Lock()
      self.vid_str_dict = {}
      await self.set_cam_counts()
      self.display_deque = deque()
      self.tf_worker = tf_worker_client(self.worker_in, self.worker_reg, )
      self.tf_w_index = await self.tf_worker.register(self.tf_worker_id, prio = 2)
      await self.tf_worker.run_out(self.tf_w_index, self.logger, self.logname)
      self.finished = False
      self.motion_frame = [0,0,0.0]
      self.last_insert_ready = 0.0
      self.last_insert_start = float('inf')
      self.old_frame_ts = 0.0
      self.old_frame_time = 0.0
      self._tasks = []
      self.x_from_cam = -1
      self.y_from_cam = -1
      self._tasks.append(asyncio.create_task(self.check_events(), name="E:check_events"))
      self._tasks.append(asyncio.create_task(self.tags_refresh(), name="E:tags_refresh"))
      self._tasks.append(asyncio.create_task(self.inserter(), name="E:inserter"))
      if self.dbline.eve_webm_doit:
        self._tasks.append(asyncio.create_task(self.make_webm(), name="E:make_webm"))
      self.inferencing_status = 0
      self.fps_limit_old = -1
      self.email_address = self.dbline.eve_alarm_email
      #print(f'Launch: eventer #{self.id}')
      while not self.got_sigint:
        if streams_redis.check_if_counts_zero('E', self.id):
          await a_break_type(BR_LONG)
          continue
        frameline = await self.dataqueue.get(timeout = 2.0)
        if frameline is None:
          continue
        if self.inferencing_status == 1:
          await a_break_type(BR_LONG)
          continue
        elif self.inferencing_status == 0:  
          self.inferencing_status = 1  
        if not self.do_run:
          break  
        if (frameline[0] is not None 
            and self.sl.greenlight(frameline[2])):
          if frameline[1].shape[:2] != (self.y_from_cam, self.x_from_cam):
            self.y_from_cam, self.x_from_cam = frameline[1].shape[:2]
            self.shared_mem.write_1_meta('aoi_xdim', self.x_from_cam)
            self.shared_mem.write_1_meta('aoi_ydim', self.y_from_cam)
            x_canvas = self.shared_mem.read_1_meta('x_canvas')
            if x_canvas and frameline[1].shape[1] > x_canvas:
              scaling = x_canvas / frameline[1].shape[1]
            else:
              scaling = 1.0  
            self.linewidth = round(4.0 / scaling)
            self.textheight = round(0.51 / scaling)
            self.textthickness = round(2.0 / scaling)  
          await self.run_one(frameline)  
        else:
          await a_break_type(BR_MEDIUM)
      await self.dataqueue.stop()
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
      await self.tf_worker.stop_out(self.tf_w_index)
      await self.tf_worker.unregister(self.tf_w_index)
      if hasattr(self, "_tasks"):
        for t in self._tasks:
          t.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
      if getattr(self, "_inq_task", None):
        self._inq_task.cancel()
        try:
          await self._inq_task
        except asyncio.CancelledError:
          pass
    except Exception as fatal:
      self.logger.error(
        'Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("async_runner crashed: %s", fatal, exc_info=True)
      self.logger.info('Restarting process...')
      while True:
        await a_break_type(BR_LONG)
        if not startup_redis.get_start_stream_busy(): 
          break
      startup_redis.set_start_stream_busy(self.id)
      os.kill(os.getpid(), SIGKILL)
    except Exception as fatal:
      self.logger.error(
        'Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("async_runner crashed: %s", fatal, exc_info=True)

  async def run_one(self, frame):
    if streams_redis.check_if_counts_zero('E', self.id):
      await a_break_type(BR_LONG)
      return()
    if streams_redis.view_from_dev('E', self.id):
      if self.fps_limit_old != (new_fps := self.shared_mem.read_1_meta('fps_limit')):
        if new_fps == 0:
          self.sl.period = 0.0
        else:
          self.sl.period = 1.0 / new_fps
        self.fps_limit_old = new_fps
      if self.do_run and frame[0]:
        await self.display_events(frame)
        await a_break_type(BR_SHORT)
    else:    
      await a_break_type(BR_LONG)
    if self.do_run and self.dbline.eve_view:
      fps = self.som.gettime()
      if fps:
        self.dbline.eve_fpsactual = fps
        streams_redis.fps_to_dev('E', self.id, fps)

  async def set_cam_counts(self):
    if any([len(self.cond_dict[x]) for x in range(2,6)]):
      add_data_count(self.type, self.id) #just switch 0 or 1
    else:
      take_data_count(self.type, self.id)
    if self.cond_dict[3]:
      add_record_count(self.type, self.id)
    else:
      take_record_count(self.type, self.id)
    await a_break_type(BR_SHORT)
    
  async def check_event(self, i, item):
    await a_break_type(BR_SHORT)
    if self.dbline.cam_virtual_fps:
      newtime = streams_redis.get_virt_time(self.id)
    else:
      newtime = time() 
    if item.end < newtime - 2 * MAX_EVENT_LENGTH:
      async with self.event_dict_lock:
        self.event_dict.pop(i, None)
      return()
    if self.shared_mem.read_1_meta('one_frame_per_event'):
      item.check_out_ts = item.end
    else:  
      if (item.end < newtime - self.shared_mem.read_1_meta('event_time_gap')
          or item.end > item.start + MAX_EVENT_LENGTH):
        item.check_out_ts = item.end
    if self.cond_dict[5]:
      predictions = await item.pred_read(max=1.0)
    else:
      predictions = None  
    if await resolve_rules(self.cond_dict[5], predictions):
      if item.remaining_alarms:
        await alarm(self.id, predictions) 
        item.remaining_alarms -= 1
    if item.check_out_ts is None:
      return()
    if predictions is None and self.cond_dict[2]:
      predictions = await item.pred_read(max=1.0)
    item.goes_to_school = await resolve_rules(self.cond_dict[2], predictions)
    if predictions is None and self.cond_dict[3]:
      predictions = await item.pred_read(max=1.0)
    if getattr(item, "video_failed", False):
      item.isrecording = False
    else:
      item.isrecording = await resolve_rules(self.cond_dict[3], predictions)
    if predictions is None and self.cond_dict[4]:
      predictions = await item.pred_read(max=1.0)
    if await resolve_rules(self.cond_dict[4], predictions):
      item.to_email = self.email_address
    else:
      item.to_email = ''
    is_done = True
    if item.goes_to_school or item.isrecording or item.to_email:
      if not await afree_quota(item.stream_creator):
        self.logger.warning(f'EV{self.id}: Did not save the event because of low quota')
        async with self.event_dict_lock:
          self.event_dict.pop(i, None)
        return()
      if item.isrecording:
        async with self.vid_deque_lock:
          if (checkbool := (self.vid_deque 
              and item.check_out_ts <= self.vid_deque[-1][2])):
            my_vid_list = [v_item for v_item in self.vid_deque 
              if (item.start <= v_item[2] +self.dbline.cam_ffmpeg_segment + 10.0  
                and item.end >= v_item[2] - 10.0)] 
            try:
              my_vid_start = my_vid_list[0][2]
            except IndexError:
              self.logger.warning(f"No matching videos for event {i}: (start={item.start},  "
                f"end={item.end}, deque={[v[2] for v in self.vid_deque]})")
              item.video_failed = True
              return()
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
              await a_break_type(BR_SHORT)
              savepath = await aiofiles.os.path.abspath(savepath)
              await a_break_type(BR_SHORT)
              async with aiofiles.open(listfilename, 'w') as f1:
                for line in my_vid_list:
                  await f1.write(
                    'file ' 
                    + await aiofiles.os.path.abspath(self.recordingspath + line[1]) 
                    + '\n'
                  )
              await a_break_type(BR_SHORT)
              cmd = [
                  'ffmpeg', '-hide_banner', '-loglevel', 'error', '-y',
                  '-f', 'concat', '-safe', '0', '-i', listfilename,
                  '-c', 'copy', temppath,
              ]
              proc = await asyncio.create_subprocess_exec(
                  *cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE
              )
              _, stderr = await proc.communicate()
              try:
                await aiofiles.os.remove(listfilename)
              except FileNotFoundError:
                pass
              if proc.returncode != 0 or not await aiofiles.os.path.exists(temppath):
                self.logger.error(
                  f"ffmpeg concat failed rc={proc.returncode}, out='{temppath}' fehlt. "
                  f"stderr: {stderr.decode(errors='ignore').strip()}"
                )
                async with self.event_dict_lock:
                  self.event_dict.pop(i, None)
                return()
              try:
                await asyncio.to_thread(os.replace, temppath, savepath)
              except OSError:
                await aioshutil.move(temppath, savepath)
            if self.dbline.eve_webm_doit:
              eventers_redis.push_to_webm(self.id, savepath)
            self.vid_str_dict[my_vid_str] = item.savename
            isdouble = False
          item.dbline.videoclip = item.savename[:-4]
          item.dbline.double = isdouble
          await item.dbline.asave()
          if not isdouble:
            proc = await asyncio.create_subprocess_exec(
              'ffmpeg', 
              '-ss', str(vid_offset), 
              '-v', 'fatal', 
              '-i', savepath, 
              '-vframes', '1', 
              '-q:v', '2', 
              savepath[:-4]+'.jpg'
            )
            await proc.wait()
        else:  
          is_done = False
      if is_done:
        await item.save(self.cond_dict)
    if is_done: 
      self.last_saved_event_end = item.check_out_ts
      async with self.event_dict_lock:
        self.event_dict.pop(i, None)

  async def check_events(self):
    try:
      while self.do_run:
        await(a_break_type(BR_LONG))
        async with self.event_dict_lock:
          check_list = list(self.event_dict.items())
        for i, item in check_list:
          await(a_break_type(BR_SHORT))
          await self.check_event(i, item)
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("check_events crashed: %s", fatal, exc_info=True)
      self.logger.info('Restarting process...')
      while startup_redis.get_start_stream_busy(): 
        await a_break_type(BR_LONG)
      startup_redis.set_start_stream_busy(self.id)
      os.kill(os.getpid(), SIGKILL)

  async def tags_refresh(self):
    try:
      while self.do_run:
        await(a_break_time(60.0))
        if self.tag_list_active != self.shared_mem.read_1_meta('school'):
          self.tag_list_active = self.shared_mem.read_1_meta('school')
          self.taglist = await database_sync_to_async(get_taglist)(self.tag_list_active)
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("tags_refresh crashed: %s", fatal, exc_info=True)
      
  async def inserter(self):
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
            self.last_insert_start = frame[2]
            detector_buffer.append(frame)
            await a_break_type(BR_SHORT)  
        if detector_buffer:
          imglist = [
            await asyncio.to_thread(
              cv.cvtColor, 
              frame[1], 
              cv.COLOR_BGR2RGB, 
            ) for frame in detector_buffer
          ]
          del frame
          await self.tf_worker.ask_pred(
            self.shared_mem.read_1_meta('school'), 
            imglist, 
            self.tf_w_index,
          )
          predictions = []
          for frame in detector_buffer:
            if len(predictions) == 0:
              predictions = await self.tf_worker.get_from_outqueue(self.tf_w_index)
            prediction = predictions[0]
            predictions = predictions[1:]
            frame = frame + [prediction]
            found = None
            margin = self.shared_mem.read_1_meta('margin')
            if not self.shared_mem.read_1_meta('one_frame_per_event'):
              async with self.event_dict_lock:
                check_list = list(self.event_dict.items())
              for j, item in check_list:
                if hasoverlap((frame[3][0] - margin, frame[3][1] + margin, 
                    frame[3][2] - margin, frame[3][3] + margin), item):
                  found = item
                  break
                await a_break_type(BR_SHORT)
            if found is None or found.check_out_ts:
              count = 0 
              async with self.event_dict_lock:
                while count in self.event_dict:
                  count += 1  
                new_event = await c_event.create(
                  self.tf_worker, 
                  self.tf_w_index, 
                  frame, 
                  margin, 
                  self.dbline, 
                  self.shared_mem.read_1_meta('school'), 
                  count, 
                  self.shared_mem.read_1_meta('shrink_factor'), 
                  self.logger, 
                )
                new_event.remaining_alarms = self.shared_mem.read_1_meta('alarm_max_nr')
                self.event_dict[count] = new_event
                await self.merge_events()
            else: 
              async with self.event_dict_lock:
                found.add_frame(frame)
                await self.merge_events()
          self.last_insert_ready = frame[2]
          self.inferencing_status = 2
          del frame
          detector_buffer.clear()
        else:
          await a_break_type(BR_SHORT)  
      return()  
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("inserter crashed: %s", fatal, exc_info=True)
      self.logger.info('Restarting process...')
      while startup_redis.get_start_stream_busy(): 
        await a_break_type(BR_LONG)
      startup_redis.set_start_stream_busy(self.id)
      os.kill(os.getpid(), SIGKILL)

  async def display_events(self, frame):
    if len(self.display_deque) >= 10: 
      self.display_deque.popleft()  
      await a_break_type(BR_SHORT)
      return()   
    self.display_deque.append(frame)
    async with self.event_dict_lock:
      display_list = [
        item for item in self.event_dict.values() if item.check_out_ts is None
      ]
    new_frame_time = self.display_deque[0][2]
    leave = ((new_frame_ts := time()) - self.old_frame_ts 
      < (new_frame_time - self.old_frame_time) * 0.75)
    self.old_frame_ts = new_frame_ts
    self.old_frame_time = new_frame_time
    if leave:
      await a_break_type(BR_SHORT)
      return()
    if (display_list 
        and (new_frame_time 
          <= self.last_insert_start + self.shared_mem.read_1_meta('sync_factor'))
        and (new_frame_time 
          > self.last_insert_ready + self.shared_mem.read_1_meta('sync_factor'))):
      await a_break_type(BR_SHORT)
      return()
    newframe = self.display_deque.popleft()
    newframe[1] = newframe[1].copy()  # Ensure the array is writable
    for item in display_list:
      predictions = await item.pred_read(max=1.0)
      if await resolve_rules(self.cond_dict[1], predictions):
        if self.shared_mem.read_1_meta('nr_of_cond_ed') <= 0:
          self.shared_mem.write_1_meta('last_cond_ed', 1)
        if await resolve_rules(
            self.cond_dict[self.shared_mem.read_1_meta('last_cond_ed')], 
            predictions, 
          ):
          colorcode= (0, 0, 255)
        else:
          colorcode= (0, 255, 0)
        tag_display_list = [(j, predictions[j]) for j in range(1, len(self.tag_list)) 
          if predictions[j] >= 0.5]
        tag_display_list.sort(key = lambda x: -x[1])
        tag_display_list = tag_display_list[:3]
        await asyncio.to_thread(
          cv.rectangle, 
          newframe[1], 
          (item[0], item[2]),
          (item[1], item[3]),
          colorcode, 
          self.linewidth, 
        )
        if item[2] < (self.dbline.cam_yres - item[3]):
          y0 = item[3] + 30 * self.textheight
        else:
          y0 = item[2] - (10 + (len(tag_display_list) - 1) * 30) * self.textheight
        if y0 > frame[1].shape[0] - 5 or y0 < 5:
          y0 = item[2] + 30 * self.textheight
        for j in range(len(tag_display_list)):
          await asyncio.to_thread(
            cv.putText, 
            newframe[1], 
            self.tag_list[tag_display_list[j][0]].name[:3]
            +' - '+str(round(tag_display_list[j][1],2)), 
            (item[0] + 5, round(y0 + j * 30 * self.textheight)), 
            cv.FONT_HERSHEY_SIMPLEX, 
            self.textheight, 
            colorcode, 
            self.textthickness, 
            cv.LINE_AA, 
          ) 
    await self.viewer_queue.put(newframe)
    del newframe  

  async def merge_events(self):
    while True:
      del_set = set()
      i_list = list(self.event_dict.items())
      j_list = i_list
      for i, event_i in i_list:
        if not event_i.check_out_ts:
          for j, event_j in j_list:
            if j > i:
              if not event_j.check_out_ts:
                if hasoverlap(event_i, event_j):
                  event_i[0] = min(event_i[0], event_j[0])
                  event_i[1] = max(event_i[1], event_j[1])
                  event_i[2] = min(event_i[2], event_j[2])
                  event_i[3] = max(event_i[3], event_j[3])
                  event_i.start = min(event_i.start, event_j.start)
                  event_i.end = max(event_i.end, event_j.end)
                  event_i.merge_frames(event_j)
                  del_set.add(j) 
      if del_set:   
        for i in del_set:
          self.event_dict.pop(i, None)
      else:
        break
      await a_break_type(BR_SHORT)

  async def make_webm(self):
    try:
      while self.do_run:
        if (mp4_file := eventers_redis.pop_from_webm(self.id)):
          mp4_file = self.recordingspath + mp4_file.decode()
          webm_file = mp4_file[:-4] + '.webm'
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
          await a_break_type(BR_SHORT)
          process = await asyncio.create_subprocess_exec(*descriptor)
          await process.wait()
        await a_break_time(10.0)
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("makewebm crashed: %s", fatal, exc_info=True)
