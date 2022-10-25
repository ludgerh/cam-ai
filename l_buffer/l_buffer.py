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

class l_buffer_not_implemented(Exception):
  def __init__(self, envi, buff, bput, bget, call):
    self.message = ('l_buffer has no implementation for envi='+envi+' buff='
      +str(buff)+' bput='+str(bput)+' buff='+str(buff)+' call='+str(call))
    super().__init__(self.message)

class l_buffer:
  redis_dict = {}

  def __init__(self, envi, buff=False, bput=False, bget=False, call=None):
    self.envi = envi
    self.buff = buff
    self.bput = bput
    self.bget = bget
    self.call = call
    self.out_event = None
    self.in_event = None
    self.out_block_wthread = None
    self.in_block_wthread = None
    implemented = True
    if self.envi == 'A':
      if self.buff:
        implemented = False
      else:
        self.storage = None
        if self.bput:
          implemented = False
        else:
          if self.bget:
            implemented = False
    elif self.envi == 'D':
      self.redis = saferedis()
      if self.buff:
        implemented = False
      else:
        self.storage = 0
        while self.storage in l_buffer.redis_dict:
          self.storage += 1
        l_buffer.redis_dict[self.storage] = 'l_buffer:'+str(self.storage)
        self.redis.delete(l_buffer.redis_dict[self.storage])
        self.out_blocked = False
        self.in_blocked = False
        if self.bput:
          self.in_event = Event()
        if self.bget:
          self.out_event = Event()
        else:
          if self.call:
            self.out_event = Event()
    else:
      implemented = False
    if not implemented:
      raise(l_buffer_not_implemented(envi, bcat, call))

  def register_callback(self):
    if self.call:
      self.call_wthread=Thread(target=self.call_worker, 
        name='l_buffer_callback_worker')
      self.call_wthread.start()

  def call_worker(self):
    self.do_run = True
    while self.do_run:
      self.out_event.wait()
      if self.do_run and self.call:
        self.call()
      self.out_event.clear()

  def get_block_worker(self):
    self.do_run = True
    while self.do_run:
      self.out_event.wait()
      #print('get_block_worker')
      self.out_blocked = False
      self.out_event.clear()

  def put_block_worker(self):
    self.do_run = True
    while self.do_run:
      self.in_event.wait()
      #print('put_block_worker')
      self.in_blocked = False
      self.in_event.clear()

  def get(self):
    if self.envi == 'A':
      while self.storage is None:
        sleep(0.1)
      return(self.storage)
    elif self.envi == 'D':
      if self.bget and not self.out_block_wthread:
        self.out_block_wthread=Thread(target=self.get_block_worker, 
          name='l_buffer_get_block_worker')
        self.out_block_wthread.start()
      ts = time()
      while (self.out_blocked 
        or (not self.redis.exists(l_buffer.redis_dict[self.storage]))):
        if (time() - ts) > 5.0:
          return(None)
        sleep(0.005)
      if self.bget:
        #print('get_block')
        self.out_blocked = True
      result = loads(self.redis.get(l_buffer.redis_dict[self.storage]))
      if self.bput: 
        #print('get_release')
        self.in_event.set()
      return(result)

  def put(self, data):
    if self.envi == 'A':
      self.storage = data
      if self.call is not None:
        self.call()
    elif self.envi == 'D': 
      if self.bput and not self.in_block_wthread:
        self.in_block_wthread=Thread(target=self.put_block_worker, 
          name='l_buffer_put_block_worker')
        self.in_block_wthread.start()
      ts = time()
      while self.in_blocked:
        if (time() - ts) > 5.0:
          return(None)
        sleep(0.005)
      if self.bput:
        #print('put_block')
        self.in_blocked = True
      self.redis.set(l_buffer.redis_dict[self.storage], dumps(data))
      if self.call or self.bget: 
        #print('put_release')
        self.out_event.set()

  def stop(self): 
    self.do_run = False
    if self.out_event: 
      self.out_event.set()
    if self.in_event: 
      self.in_event.set()
