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
v1.6.6 01.03.25
"""

import asyncio
import aiofiles
import numpy as np
import cv2 as cv
from asgiref.sync import sync_to_async
from multiprocessing import Process
from threading import Lock as t_lock
from logging import getLogger
from time import time
from setproctitle import setproctitle
import gc
from django.utils import timezone
from django.forms.models import model_to_dict
from globals.c_globals import tf_workers
from tf_workers.c_tf_workers import tf_worker_client
from .redis import my_redis as trainers_redis

#from threading import enumerate 

async def clean_fits():
  from .models import fit
  async for item in fit.objects.all():
    if item.status == 'Queuing' or item.status == 'Working':
      item.status = 'Stopped'
      await item.asave(update_fields=['status', ])        

#***************************************************************************
#
# trainers server
#
#***************************************************************************
def decode_and_convert_image(myimage_bytes):
  img = cv.imdecode(np.frombuffer(myimage_bytes, dtype=np.uint8), cv.IMREAD_UNCHANGED)
  return cv.cvtColor(img, cv.COLOR_BGR2RGB)

from tools.c_spawn import spawn_process

CHUNK_SIZE = 32

def _chunked(seq, n):
  for i in range(0, len(seq), n):
    yield seq[i:i+n]

class trainer(spawn_process):
  def __init__(self, idx, worker_inqueue, worker_registerqueue, glob_lock):
    self.id = idx
    self.worker_in = worker_inqueue
    self.worker_reg = worker_registerqueue
    self.glob_lock = glob_lock
    if self.id == 1:
      self.glob_lock.acquire()
    super().__init__()
      
  async def update_predictions(self, school_nr, last_fit):
    with self.glob_lock:
      if trainers_redis.get_predict_proc_active(school_nr): 
        return()
      trainers_redis.set_predict_proc_active(school_nr, True)
    from .models import trainframe
    from tf_workers.models import school
    school_dbline = await school.objects.aget(id = school_nr)
    framelines = trainframe.objects.filter(school = school_nr)
    frames = []
    async for item in framelines.aiterator(chunk_size=1000):
      if item.last_fit != school_dbline.last_fit:
        frames.append(item)
    if frames:  
      self.logger.info(
        f'TR{self.id}: Re-inferencing {len(frames)} frames of school #{school_nr}'
      )  
      for chunk in _chunked(frames, CHUNK_SIZE):
        imglist = []
        frame_ids = []
        for item in chunk:
          await asyncio.sleep(0)
          imagepath = school_dbline.dir + 'frames/' + item.name 
          async with aiofiles.open(imagepath, mode = "rb") as f:
            myimage = await f.read()
          myimage = await asyncio.to_thread(decode_and_convert_image, myimage) 
          frame_ids.append(item.id) 
          imglist.append(myimage)
        await self.tf_worker.ask_pred(
          school_nr, 
          imglist, 
          self.tf_w_index,
        )
        received = []
        for idx in frame_ids:
          await asyncio.sleep(0)
          if not received:
            received = (await asyncio.wait_for(
              self.tf_worker.get_from_outqueue(self.tf_w_index),
              timeout=60
            )).tolist()
          prediction = received.pop(0) 
          frameline = await trainframe.objects.aget(id = idx)
          frameline.last_fit = school_dbline.last_fit
          for i in range(10):
            setattr(frameline, f"pred{i}", prediction[i])
          await frameline.asave(
            update_fields=["last_fit"] + [f"pred{i}" for i in range(10)], 
          )
      self.logger.info(
        f'TR{self.id}: Finished re-inferencing of school #{school_nr}'
      )  
    trainers_redis.set_predict_proc_active(school_nr, False)
    
              
  async def async_runner(self): 
    try:
      from tools.c_logger import alog_ini
      from tools.l_tools import ts2mysqltime
      from tools.l_break import a_break_time, a_break_type, BR_LONG
      from .models import trainer as dbtrainer, trainframe
      self.dbline = await dbtrainer.objects.aget(id = self.id)
      setproctitle('CAM-AI-Trainer #'+str(self.id))
      self.do_run = True
      self.mylock = t_lock()
      trainers_redis.set_trainerqueue(self.id, [])
      self.job_queue_list = []
      train_once_gpu = None
      train_once_remote = None
      self.logname = 'trainer #'+str(self.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      self.tf_worker = tf_worker_client(self.worker_in, self.worker_reg)
      self.tf_w_index = await self.tf_worker.register(1)
      await self.tf_worker.run_out(self.tf_w_index, self.logger, self.logname)
      self.finished = False
      self.job_queue = asyncio.Queue()
      self.school_cache = {}
      self.frames_cache = {}
      asyncio.create_task(self.job_queue_thread(), name = 'job_queue_thread')
      #print('Launch: trainer')
      await super().async_runner() 
      if self.dbline.t_type in {2, 3}:
        self.process_dict = {}
      while self.do_run:
        timestr = ts2mysqltime(time())
        if((self.dbline.startworking < timestr) 
            and (self.dbline.stopworking > timestr)
            and self.dbline.running):
          if self.dbline.t_type in {2, 3}:
            for item in list(self.process_dict):
              if not self.process_dict[item][0].is_alive():
                filterdict = {
                  'school' : self.process_dict[item][1].id,
                  'train_status' : 1,
                }
                if not self.process_dict[item][1].ignore_checked:
                  filterdict['checked'] = True
                await trainframe.objects.filter(**filterdict).aupdate(train_status = 2)
                myschool.l_rate_divisor = 10000.0
                await myschool.asave(update_fields=['l_rate_divisor'])
                del self.process_dict[item]
          try:  
            myschool, myfit = await asyncio.wait_for(self.job_queue.get(), timeout = 1.0)
          except asyncio.TimeoutError:
            continue  
          if self.dbline.t_type == 1:
            if train_once_gpu is None:
              from plugins.train_worker_gpu.train_worker_gpu import train_once_gpu
            train_process = Process(target = train_once_gpu, args = (
              myschool, 
              myfit, 
              self.dbline.gpu_nr,
              self.dbline.gpu_mem_limit,
            ), 
            kwargs = {
              'trainer_nr' : self.id,
            }
            )
            train_process.start()
            await asyncio.to_thread(train_process.join)
            trainresult = (train_process.exitcode)
          elif self.dbline.t_type in {2, 3}:
            if train_once_remote is None:
              from .train_worker_remote import train_once_remote
            my_trainer = train_once_remote(
                myschool, 
                myfit, 
                self.dbline,
            )
            train_process = Process(target = my_trainer.run)
            train_process.start()
            self.process_dict[train_process.pid] = ((train_process, myschool))
          if myschool.delegation_level <= 1:  
            await self.update_predictions(myschool.id, myschool.last_fit) 
          with self.mylock:
            self.job_queue_list.remove(myschool.id)
          trainers_redis.set_trainerqueue(self.id, self.job_queue_list)
          await asyncio.to_thread(gc.collect)
        await a_break_time(10.0)
      await self.tf_worker.stop_out(self.tf_w_index)
      await self.tf_worker.unregister(self.tf_w_index) 
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
    except Exception as fatal:
      self.logger.error(
        'Error in process: ' + self.logname)
      self.logger.critical("async_runner crashed: %s", fatal, exc_info=True)

  async def job_queue_thread(self):
    try:
      from tools.l_break import a_break_time, a_break_type, BR_LONG
      from globals.c_globals import trainers
      from tf_workers.models import school
      from .models import trainframe, fit
      if self.id == 1:  
        schoollines = await sync_to_async(list)(school.objects.filter(
          active=True, 
          delegation_level = 1, 
        ))
        for s_item in schoollines: 
          trainers_redis.set_predict_proc_active(s_item.id, False)
        self.glob_lock.release()    
      while self.do_run:
        schoollines = await sync_to_async(list)(school.objects.filter(active=True))
        for s_item in schoollines:
          await s_item.arefresh_from_db()
          if s_item.delegation_level == 1:  
            await self.update_predictions(s_item.id, s_item.last_fit) 
          if s_item.id in self.school_cache:
            school_change = (
              await sync_to_async(model_to_dict)(s_item) != self.school_cache[s_item.id]
            )
            self.school_cache[s_item.id] = await sync_to_async(model_to_dict)(s_item)
          else:
            school_change = True
            self.school_cache[s_item.id] = await sync_to_async(model_to_dict)(s_item)
          if s_item.id in self.frames_cache:
            frames_change = (
              trainers_redis.get_last_frame(s_item.id) != self.frames_cache[s_item.id]
            )
            self.frames_cache[s_item.id] = trainers_redis.get_last_frame(s_item.id)
          else:
            frames_change = True
            self.frames_cache[s_item.id] = trainers_redis.get_last_frame(s_item.id)
          if not (school_change or frames_change):
            await a_break_type(BR_LONG)
            continue
          for t_item in trainers:
            if s_item.id in trainers[t_item].getqueueinfo():
              self.logger.warning(
                f'TR{self.id}: School #{s_item.id} not inserted into Trainer Queue '
                + 'because already in.'
              )  
              self.school_cache[s_item.id] = model_to_dict(s_item)
              continue
          filterdict = {
            'school' : s_item.id,
            'train_status' : 0,}
          if not s_item.ignore_checked:
            filterdict['checked'] = True
          undone_qs = trainframe.objects.filter(**filterdict)
          if await s_item.trainers.filter(id=self.id).aexists():
            run_condition = (
              await trainframe.objects.filter(school=s_item.id).acount() > 0
            )
            if run_condition:
              await sync_to_async(s_item.trainers.remove)(self.dbline)
          else:
            run_condition = (
              await undone_qs.acount() >= s_item.trigger
              and not s_item.id in self.job_queue_list
              and s_item.delegation_level == 1
            )
          if run_condition:
            await undone_qs.aupdate(train_status=1)
            myfit = fit(
              made=timezone.now(), 
              school = s_item.id, 
              status = 'Queuing',
            )
            await myfit.asave() 
            with self.mylock:
              self.job_queue_list.append(s_item.id)
            trainers_redis.set_trainerqueue(self.id, self.job_queue_list)
            await self.job_queue.put((s_item, myfit)) 
        try:
          await a_break_time(10.0)
        except  asyncio.exceptions.CancelledError:
          pass
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + str(self.id)
      )
      self.logger.critical("job_queue_thread crashed: %s", fatal, exc_info=True)

#***************************************************************************
#
# trainers client
#
#***************************************************************************

  def getqueueinfo(self):
    return(trainers_redis.get_trainerqueue(self.id))
