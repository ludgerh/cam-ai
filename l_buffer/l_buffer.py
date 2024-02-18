# Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
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

import pickle
import numpy as np
from os import getpid
from time import sleep, time
from multiprocessing import Lock
from threading import Thread
from tools.c_redis import saferedis
from traceback import format_exc

class l_buffer:
  redis_list = []

  def __init__(self, itemtype=None, block=False, call=None):
    self.block = block
    self.call = call
    self.redis = saferedis()
    self.itemtype = itemtype    
    self.blockdelay = 0.01  
    i = 0
    while i in l_buffer.redis_list:
      i += 1
    l_buffer.redis_list.append(i)
    if itemtype is None:
      self.my_lock = Lock()
      self.storage = ('l_buffer:'+str(i)+':bytes', 'l_buffer:'+str(i)+':object')
      self.redis.delete(self.storage[0])
      self.redis.delete(self.storage[1])
    else:
      if self.itemtype == 0:
        storagedim = 1
      elif self.itemtype == 1:
        self.first_time = True
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
        if message['data'] == b'D':
          break
        elif message['data'] == b'T':
          print('+', end = '')
          try:
            self.call()
          except:
            print(format_exc()) 
          print('-', end = '')
          continue
      sleep(0.01) 
    print('Message Handler finished')  
    
  def get(self):
    if self.block or (self.itemtype == 1 and self.first_time):
      ts1 = time()
      while (not self.redis.exists(self.storage[0])):
        if time() - ts1 > 5:
          return(None)
        else:  
          sleep(self.blockdelay)
          if self.blockdelay < 1.0:
            self.blockdelay += 0.01       
      self.blockdelay = 0.01  
    if self.itemtype is None:
      with self.my_lock:
        if (objdata := self.redis.rpop(self.storage[1])):
          objdata = pickle.loads(objdata)
        result = (
          self.redis.rpop(self.storage[0]),
          objdata,
        )
    elif self.itemtype == 0:
      result = np.frombuffer(self.redis.get(self.storage[0]), dtype=np.uint8)
    elif self.itemtype == 1:
      if self.first_time:
        self.shape = (
          int(self.redis.get(self.storage[3])),
          int(self.redis.get(self.storage[4])),
          3,
        )
        self.first_time = False
      while (redis_result := self.redis.get(self.storage[0])) is None:
        sleep(1.0)
      result = (
        int(redis_result),
        np.frombuffer(
          self.redis.get(self.storage[1]), 
          dtype=np.uint8).reshape(self.shape
        ),
        float(self.redis.get(self.storage[2]))
      )
    if self.block:
      self.redis.delete(self.storage[0])
    return(result)

  def put(self, bytedata=None, objdata=None, data=None):
    if self.itemtype is None:
      with self.my_lock:
        if bytedata:
          self.redis.lpush(self.storage[0], bytedata)
        else:
          self.redis.lpush(self.storage[0], b'')
        if objdata:
          self.redis.lpush(self.storage[1], pickle.dumps(objdata))
        else:
          self.redis.lpush(self.storage[1], b'')
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
      
  def send_death_pill(self):  
    if self.call: 
      self.redis.publish(self.storage[0], 'D') #Trigger  
      
  def empty(self): 
    with self.my_lock:
      if self.redis.llen(self.storage[0]):
        return(False)
      if self.redis.llen(self.storage[1]):
        return(False)
    return(True)   
    
  def qsize(self):
    return(max(
      self.redis.llen(self.storage[0]), 
      self.redis.llen(self.storage[1]), 
    ))  

  def stop(self):
    if self.call:
      print('LBuffer-----', "self.send_death_pill()")
      self.send_death_pill()
      print('LBuffer-----', "self.do_run = False")
      self.do_run = False
      print('LBuffer-----', "self.thread.join()")
      self.thread.join()
      print('LBuffer-----', "Done")
        
