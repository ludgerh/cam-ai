# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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

# l_buffer.py V0.9.13 13.06.2023

"""
block = Block get() until new data
When using this, stop() must be called from the getting process to finalize 
shutdown.

call = Callback (True or False)
When using this, stop() must be called from the getting process to finalize 
shutdown.
"""

import numpy as np
from os import getpid
from time import sleep, time
from threading import Thread
from tools.c_redis import saferedis
from traceback import format_exc

class l_buffer:
  redis_list = []

  def __init__(self, itemtype, block=False, call=None):
    self.block = block
    self.call = call
    self.redis = saferedis()
    self.itemtype = itemtype    
    self.blockdelay = 0.01  
    if itemtype == 1:
      self.first_time = True
    i = 0
    while i in l_buffer.redis_list:
      i += 1
    l_buffer.redis_list.append(i)
    if self.itemtype == 0:
      storagedim = 1
    elif self.itemtype == 1:
      storagedim = 5
    self.storage = []  
    for j in range(storagedim):      
      self.storage.append('l_buffer:'+str(i)+':'+str(j))
    for item in self.storage:
      self.redis.delete(item)
    if self.call:
      self.do_run = True
      self.p = self.redis.pubsub(ignore_subscribe_messages=True)
      self.p.subscribe(self.storage[0])
      self.thread = Thread(target=self.message_handler, name='L_Buffer_Thread')
      self.thread.start()
    
  def message_handler(self):
    while self.do_run:
      message = self.p.get_message()
      if message:
        if message['data'] == b'T':
          self.call()
        else:  
          sleep(0.01) 
    
  def get(self):
    if self.block or self.first_time:
      ts1 = time()
      while (not self.redis.exists(self.storage[0])):
        if time() - ts1 > 5:
          return(None)
        else:  
          sleep(self.blockdelay)
          if self.blockdelay < 1.0:
            self.blockdelay += 0.01       
      self.blockdelay = 0.01  
    if self.itemtype == 0:
      result = np.frombuffer(self.redis.get(self.storage[0]), dtype=np.uint8)
    elif self.itemtype == 1:
      if self.first_time:
        self.shape = (
          int(self.redis.get(self.storage[3])),
          int(self.redis.get(self.storage[4])),
          3,
        )
        self.first_time = False
      result = (
        int(self.redis.get(self.storage[0])),
        np.frombuffer(
          self.redis.get(self.storage[1]), 
          dtype=np.uint8).reshape(self.shape
        ),
        float(self.redis.get(self.storage[2]))
      )
    if self.block:
      self.redis.delete(self.storage[0])
    return(result)

  def put(self, data):
    if self.itemtype == 0:
      self.redis.set(self.storage[0], data.tobytes())
    elif self.itemtype == 1:
      if self.first_time:
        self.redis.set(self.storage[4], data[1].shape[1])
        self.redis.set(self.storage[3], data[1].shape[0])
        self.first_time = False
      self.redis.set(self.storage[2], data[2])
      self.redis.set(self.storage[1], data[1].tobytes())
      self.redis.set(self.storage[0], data[0])
    if self.call: 
      self.redis.publish(self.storage[0], 'T') #Trigger

  def stop(self):
    if self.call:
      self.do_run = False
      self.thread.join()
        
