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

import gc
from multiprocessing import Process, Queue
from threading import Thread, Lock as t_lock
from queue import Queue as threadqueue, Empty
from signal import signal, SIGINT, SIGTERM, SIGHUP
from traceback import format_exc
from logging import getLogger
from time import sleep, time
from setproctitle import setproctitle
from django.utils import timezone
from django.db import connections
from startup.startup import trainers
from tools.c_logger import log_ini
from tools.l_tools import (
  protected_db, 
  protect_list_db, 
  QueueUnknownKeyword, 
  ts2mysqltime, 
  djconf,
)
from tf_workers.models import school
from users.models import userinfo
from users.userinfo import free_quota
from schools.c_schools import school_dict, school as school_class
from .models import trainer as dbtrainer, trainframe, fit, epoch
if djconf.getconfigbool('local_trainer', False):
  if djconf.getconfigbool('local_gpu', False):
    from plugins.train_worker_gpu.train_worker_gpu import train_once_gpu
from .train_worker_remote import train_once_remote
from .redis import my_redis

#from threading import enumerate

short_brake = djconf.getconfigfloat('short_brake', 0.01)
long_brake = djconf.getconfigfloat('long_brake', 1.0)
      
      
fitstochange = fit.objects.filter(status='Queuing')
fitstochange = fitstochange | fit.objects.filter(status='Working')
for fititem in fitstochange:
  fititem.status = 'Stopped'
  fititem.save(update_fields=['status', ])
                    
                    

def sigint_handler(signal, frame):
  #print ('TFWorkers: Interrupt is caught')
  pass

#***************************************************************************
#
# trainers server
#
#***************************************************************************

class trainer():
  
  def __init__(self, dbline):
    self.inqueue = Queue()
    self.id = dbline.id
    self.mylock = t_lock()
    my_redis.set_trainerqueue(self.id, [])
    self.job_queue_list = []

  def in_queue_thread(self):
    try:
      while True:
        received = self.inqueue.get()
        #print('Trainer:', received)
        if (received[0] == 'stop'):
          self.do_run = False
          while not self.inqueue.empty():
            received = self.inqueue.get()
          break
        else:
          raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error('Error in process: ' + self.logname + ' (inqueue)')
      self.logger.error(format_exc())

  def job_queue_thread(self):
    try:
      while self.do_run:
        schoollines = school.objects.filter(
          active = True,
          trainers = self.id,
        )
        protect_list_db(schoollines)
        for s_item in schoollines:
          if s_item.id not in school_dict:
            school_dict[s_item.id] = school_class(s_item.id)
          with school_dict[s_item.id].lock:
            for t_item in trainers:
              if s_item.id in trainers[t_item].getqueueinfo():
                break
            filterdict = {
              'school' : s_item.id,
              'train_status' : 0,}
            if not s_item.ignore_checked:
              filterdict['checked'] = True
            undone = trainframe.objects.filter(**filterdict)
            if s_item.trainer_nr == self.id:
              run_condition = trainframe.objects.filter(school=s_item.id).count()
            else:
              run_condition = (protected_db(undone.count) >= s_item.trigger 
                and not self.job_queue_list
                and s_item.delegation_level == 1)
            if run_condition:
              undone.update(train_status=1)
              s_item.trainer_nr = 0
              s_item.save(update_fields=["trainer_nr"])
              myfit = fit(made=timezone.now(), 
                school = s_item.id, 
                status = 'Queuing',
              )
              myfit.save() 
              with self.mylock:
                self.job_queue_list.append(s_item.id)
              my_redis.set_trainerqueue(self.id, self.job_queue_list)
              self.job_queue.put((s_item, myfit)) 
        sleep(10.0)
    except:
      self.logger.error('Error in process: ' + self.logname + ' (job_queue_thread)')
      self.logger.error(format_exc())

  def run(self):
    self.do_run = True
    self.run_process = Process(target=self.runner, )
    connections.close_all()
    self.run_process.start()

  def runner(self):
    try:
      self.dbline = dbtrainer.objects.get(id=self.id)
      Thread(target=self.in_queue_thread, name='Trainer_InQueueThread').start()
      signal(SIGINT, sigint_handler)
      signal(SIGTERM, sigint_handler)
      signal(SIGHUP, sigint_handler)
      self.logname = 'trainer #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      log_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Trainer #'+str(self.dbline.id))
      self.finished = False
      self.job_queue = threadqueue()
      Thread(
        target=self.job_queue_thread, 
        name='Trainer_JobQueueThread #' + str(self.id),
      ).start()
      while self.do_run:
        self.dbline = protected_db(dbtrainer.objects.get, kwargs = {'id' : self.id, })
        timestr = ts2mysqltime(time())
        if((self.dbline.startworking < timestr) 
            and (self.dbline.stopworking > timestr)
            and self.dbline.running):
          try:
            tempread = self.job_queue.get(timeout=1.0)
            myschool = tempread[0]
            myfit = tempread[1]
            if self.dbline.t_type == 1:
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
            elif (self.dbline.t_type in {2, 3}):
              my_tor = train_once_remote(
                myschool, 
                myfit, 
                self.dbline,
                self.logger,
              )
              train_process = Process(target = my_tor.run)
              train_process.start()
              trainresult = 0
            if not trainresult:
              filterdict = {
                'school' : myschool.id,
                'train_status' : 1,
              }
              if not myschool.ignore_checked:
                filterdict['checked'] = True
              protected_db(
                trainframe.objects.filter(**filterdict).update, 
                kwargs = {'train_status' : 2}
              )
              myschool.l_rate_start = '1e-6'
              myschool.save(update_fields=['l_rate_start'])
              #myuserinfo = userinfo.objects.get(user=myschool.creator)
              #myuserinfo.pay_tokens -= 1
              #myuserinfo.save(update_fields=['pay_tokens'])
            with self.mylock:
              self.job_queue_list.remove(myschool.id)
            my_redis.set_trainerqueue(self.id, self.job_queue_list)
            gc.collect()
          except Empty:
            pass
        sleep(10.0)
      self.finished = True
      #for thread in enumerate(): 
      #  print(thread)
      self.logger.info('Finished Process '+self.logname+'...')
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())
  
  def stop(self):
    self.inqueue.put(('stop',))
    self.run_process.join()

#***************************************************************************
#
# trainers client
#
#***************************************************************************

  def getqueueinfo(self):
    return(my_redis.get_trainerqueue(self.id))
