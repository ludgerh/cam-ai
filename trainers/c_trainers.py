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
from multiprocessing import Process
from threading import Lock as t_lock
from logging import getLogger
from time import time
from traceback import format_exc
from setproctitle import setproctitle
import gc
from django.utils import timezone
#from .models import trainframe, fit
from .redis import my_redis

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

from tools.c_spawn import spawn_process

class trainer(spawn_process):
  def __init__(self, idx, ):
    self.id = idx
    super().__init__()

  async def async_runner(self): 
    try:
      from tools.c_logger import alog_ini
      from tools.l_tools import ts2mysqltime
      from tools.l_break import a_break_time
      from .models import trainer as dbtrainer, trainframe
      self.dbline = await dbtrainer.objects.aget(id = self.id)
      setproctitle('CAM-AI-Trainer #'+str(self.id))
      self.do_run = True
      self.mylock = t_lock()
      my_redis.set_trainerqueue(self.id, [])
      self.job_queue_list = []
      train_once_gpu = None
      train_once_remote = None
      self.logname = 'trainer #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      self.finished = False
      self.job_queue = asyncio.Queue()
      asyncio.create_task(self.job_queue_thread(), name = 'job_queue_thread')
      #print('Launch: trainer')
      await super().async_runner() 
      while self.do_run:
        timestr = ts2mysqltime(time())
        if((self.dbline.startworking < timestr) 
            and (self.dbline.stopworking > timestr)
            and self.dbline.running):
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
            train_process.join()
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
            train_process.join()
            trainresult = 0
          if not trainresult:
            filterdict = {
              'school' : myschool.id,
              'train_status' : 1,
            }
            if not myschool.ignore_checked:
              filterdict['checked'] = True
            await trainframe.objects.filter(**filterdict).aupdate(train_status = 2)
            myschool.l_rate_divisor = 10000.0
            await myschool.asave(update_fields=['l_rate_divisor'])
          with self.mylock:
            self.job_queue_list.remove(myschool.id)
          my_redis.set_trainerqueue(self.id, self.job_queue_list)
          await asyncio.to_thread(gc.collect)
        await a_break_time(10.0)
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc()) 

  async def job_queue_thread(self):
    try:
      from tools.l_break import a_break_time
      from globals.c_globals import trainers
      from tf_workers.models import school
      from .models import trainframe, fit
      while self.do_run:
        #if trainers is None:
        #  await a_break_time(10.0)
        #  continue
        schoollines = school.objects.filter(
          active = True,
          trainers = self.id,
        )
        async for s_item in schoollines:
          await s_item.arefresh_from_db()
          do_continue = False
          for t_item in trainers:
            if s_item.id in trainers[t_item].getqueueinfo():
              self.logger.warning(
                '!!!!! School #' + str(s_item.id) 
                + ' not inserted into Trainer Queue because already in.')
              do_continue = True
              break
          if do_continue:
            continue    
          filterdict = {
            'school' : s_item.id,
            'train_status' : 0,}
          if not s_item.ignore_checked:
            filterdict['checked'] = True
          undone = trainframe.objects.filter(**filterdict)
          if s_item.trainer_nr == self.id:
            run_condition = await trainframe.objects.filter(school=s_item.id).acount()
          else:
            run_condition = (await undone.acount() >= s_item.trigger 
              and not self.job_queue_list
              and s_item.delegation_level == 1)
          if run_condition:
            await undone.aupdate(train_status=1)
            s_item.trainer_nr = 0
            await s_item.asave(update_fields=["trainer_nr"])
            myfit = fit(made=timezone.now(), 
              school = s_item.id, 
              status = 'Queuing',
            )
            await myfit.asave() 
            with self.mylock:
              self.job_queue_list.append(s_item.id)
            my_redis.set_trainerqueue(self.id, self.job_queue_list)
            await self.job_queue.put((s_item, myfit)) 
        try:
          await a_break_time(10.0)
        except  asyncio.exceptions.CancelledError:
          pass  
    except:
      from traceback import format_exc
      self.logger.error('Error in process: ' + self.logname + ' (job_queue_thread)')
      self.logger.error(format_exc())

#***************************************************************************
#
# trainers client
#
#***************************************************************************

  def getqueueinfo(self):
    return(my_redis.get_trainerqueue(self.id))
