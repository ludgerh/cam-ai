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

# l_buffer.py V0.9.9 31.03.2023

"""
Categories
envi = Running Environment Conditions
  A: Single Thread
  B: MultiThread
  C: MultiProcess
  D: Redis

buff = Use Buffer, Yes or no

bput = Block put() until space avcailable
When using this, stop() must be called from the putting process to finalize 
shutdown.
When used together with Callback, make sure the stop of the getting process is 
called first.
and the stop of the putting process later. Otherwise: One extra callback...

bget = Block get() until new data
When using this, stop() must be called from the getting process to finalize 
shutdown.

call = Callback (True or False)
When using this, stop() must be called from the getting process to finalize 
shutdown.
"""
from tools.c_redis import saferedis
from pickle import dumps, loads
from multiprocessing import Event
from threading import Thread
from time import sleep, time
from collections import deque
from traceback import format_exc

class l_buffer_not_implemented(Exception):
  def __init__(self, envi, bput, bget, quota, call):
    self.message = ('l_buffer has no implementation for envi=' + envi
      +' bput=' + str(bput) + ' bget=' + str(bget) + ' quota=' + str(quota)+' call=' + str(call))
    super().__init__(self.message)

class l_buffer:
  redis_dict = {}

  def __init__(self, envi, bput=False, bget=False, quota=False, call=None):
    self.envi = envi
    self.bput = bput
    self.bget = bget
    self.bget = bget
    self.quota = quota
    self.call = call
    self.get_event = None
    self.put_event = None
    self.get_block_wthread = None
    self.put_block_wthread = None
    implemented = True
    if self.envi == 'A':
      self.storage = None
      if self.bput:
        implemented = False
      elif self.bget:
        implemented = False
      elif self.quota:
        implemented = False
    elif self.envi == 'D':
      self.redis = saferedis()
      self.storage = 0
      while self.storage in l_buffer.redis_dict:
        self.storage += 1
      l_buffer.redis_dict[self.storage] = 'l_buffer:'+str(self.storage)
      self.redis.delete(l_buffer.redis_dict[self.storage])
      if self.bget:
        self.get_blocked = False
      if self.bput:  
        self.put_blocked = False
      if (self.bput or self.quota):
        self.put_event = Event()
      if self.bget or self.call:
        self.get_event = Event()
      self.do_run = True
    else:
      implemented = False
    if not implemented:
      raise(l_buffer_not_implemented(self.envi, self.bput, self.bget, 
        self.quota, self.call))
      
  def start_quota(self):
    self.quota_list = [1, ]  
    self.delivered = True   
    self.quota_wthread=Thread(target=self.quota_worker, name='l_buffer_quota_worker')
    self.quota_wthread.start() 
    
  def get_quota(self):
    return(sum(self.quota_list) / len(self.quota_list))

  def register_callback(self):
    if self.call:
      self.call_wthread=Thread(target=self.call_worker, name='l_buffer_callback_worker')
      self.call_wthread.start()

  def quota_worker(self):
    self.do_run = True
    while self.do_run:
      self.put_event.wait()
      #print('quota_worker')
      self.delivered = True
      self.put_event.clear()

  def call_worker(self):
    self.do_run = True
    #print('Start')
    #print(self.do_run)
    while self.do_run:
      self.get_event.wait()
      #print(time())
      if self.do_run and self.call:
        self.call()
      self.get_event.clear()
    #print('Stop')

  def get_block_worker(self):
    self.do_run = True
    while self.do_run:
      self.get_event.wait()
      #print('get_block_worker')
      self.get_blocked = False
      self.get_event.clear()

  def put_block_worker(self):
    self.do_run = True
    while self.do_run:
      #print('put_block_worker')
      if self.bput:
        self.put_blocked = False
        self.put_event.clear()

  def get(self):
    if self.envi == 'A':
      while self.storage is None:
        sleep(0.1)
      return(self.storage)
    elif self.envi == 'D':
      if self.bget and not self.get_block_wthread:
        self.get_block_wthread=Thread(target = self.get_block_worker, 
          name = 'l_buffer_get_block_worker')
        self.get_block_wthread.start()
      if (not self.redis.exists(l_buffer.redis_dict[self.storage])):
        return(None)
      if self.bget:
        ts = time()
        blockdelay = 0.005
        while self.get_blocked:
          if (time() - ts) > 5.0:
            return(None)
          sleep(blockdelay)
          blockdelay += 0.005
        #print('get_block')
        self.get_blocked = True
      result = loads(self.redis.get(l_buffer.redis_dict[self.storage]))
      if (self.bput or self.quota): 
        #print('get_release')
        self.put_event.set()
      return(result)

  def put(self, data):
    if self.envi == 'A':
      self.storage = data
      if self.call is not None:
        self.call()
    elif self.envi == 'D': 
      if self.bput:
        if not self.put_block_wthread:
          self.put_block_wthread=Thread(target = self.put_block_worker, 
            name = 'l_buffer_put_block_worker')
          self.put_block_wthread.start()
      if self.bput:
        ts = time()
        blockdelay = 0.005
        while self.put_blocked:
          if (time() - ts) > 5.0:
            return(None)
          sleep(blockdelay)
          blockdelay += 0.005
        #print('put_block')
        self.put_blocked = True
      self.redis.set(l_buffer.redis_dict[self.storage], dumps(data))
      if self.call or self.bget: 
        #print('put_release')
        self.get_event.set()
      if self.quota:
        if len(self.quota_list) >= 100:
          del self.quota_list[0]
        if self.delivered:
          self.quota_list.append(1)
        else:
          self.quota_list.append(0)
        self.delivered = False

  def stop(self): 
    self.do_run = False
    if self.get_event: 
      self.get_event.set()
    if self.put_event: 
      self.put_event.set()
