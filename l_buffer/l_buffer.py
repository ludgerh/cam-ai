"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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


"""
block = Block get() until new data
When using this, stop() must be called from the getting process to finalize 
shutdown.

call = Callback (True or False)
When using this, stop() must be called from the getting process to finalize 
shutdown.

queue = Set up Redis Queue
If None, the values are not buffered
"""

import pickle
import numpy as np
from time import sleep, time
from multiprocessing import Lock
from threading import Thread
from tools.c_redis import saferedis

class l_buffer():
  redis_list = []

  def __init__(self, block=False, call=None, queue=None, timeout=None):
    self.block = block
    self.call = call
    self.queue = queue
    self.timeout = timeout
    self.redis = saferedis() 
    self.blockdelay = 0.01  
    i = 0
    while i in l_buffer.redis_list:
      i += 1
    l_buffer.redis_list.append(i)
    self.my_lock = Lock()
    self.storage = (
      'l_buffer:' + str(i) + ':bytes', 
      'l_buffer:' + str(i) + ':object',
      'l_buffer:' + str(i) + ':bytes_2',
    )
    self.redis.delete(self.storage[0])
    self.redis.delete(self.storage[1])
    self.redis.delete(self.storage[2])
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
          self.call()
          continue
      sleep(0.01) 
    
  def get(self):
    if self.block:
      ts1 = time()
      while (not self.redis.exists(self.storage[0])):
        if time() - ts1 > 5:
          return(None)
        else:  
          sleep(self.blockdelay)
          if self.blockdelay < 1.0:
            self.blockdelay += 0.01  
      self.blockdelay = 0.01  
    #with self.my_lock:
    if self.my_lock.acquire(timeout = self.timeout):
      if self.queue:
        bytedata = self.redis.rpop(self.storage[0])
        objdata = self.redis.rpop(self.storage[1])
        bytedata2 = self.redis.rpop(self.storage[2])
      else:
        bytedata = self.redis.get(self.storage[0])
        objdata = self.redis.get(self.storage[1])
        bytedata2 = self.redis.get(self.storage[2])
      if objdata:
        objdata = pickle.loads(objdata)
      if bytedata2:
        result = (bytedata, objdata, bytedata2)  
      else:  
        result = (bytedata, objdata)
      self.my_lock.release()
    else:
      result = None  
    if self.block:
      if not self.queue:
        self.redis.delete(self.storage[0])
    return(result)

  def put(self, bytedata=b'', objdata=None, bytedata2=b''):
    if objdata:
      objdata = pickle.dumps(objdata)
    else:
      objdata = b''  
    #with self.my_lock:
    if self.my_lock.acquire(timeout = self.timeout):
      if self.queue:
        self.redis.lpush(self.storage[0], bytedata)
        self.redis.lpush(self.storage[1], objdata)
        self.redis.lpush(self.storage[2], bytedata2)
      else:  
        self.redis.set(self.storage[0], bytedata)
        self.redis.set(self.storage[1], objdata)
        self.redis.set(self.storage[2], bytedata2)
      if self.call: 
        self.redis.publish(self.storage[0], 'T') #Trigger
      self.my_lock.release()
      
  def send_death_pill(self):  
    if self.call: 
      self.redis.publish(self.storage[0], 'D') #Trigger  
      
  def empty(self): 
    with self.my_lock:
      if self.queue:
        result = not self.redis.llen(self.storage[0])
      else:  
        result =  not self.redis.get(self.storage[0])
    return(result)   
    
  def qsize(self):
    if self.queue:
      result = self.redis.llen(self.storage[0])
    else:  
      if self.redis.get(self.storage[0]):
        result = 1
      else:
        result = 0  
    return(result)  

  def stop(self):
    if self.call:
      self.send_death_pill()
      self.do_run = False
      self.thread.join()
      
class c_buffer(l_buffer):
  
  def put(self, frame):
    bytes = frame[1].tobytes()
    objects = [frame[0], frame[1].shape[0], frame[1].shape[1]] + list(frame[2:])
    super().put(bytedata=bytes, objdata=objects)
    
  def get(self):
    frame = super().get()
    if frame and frame[0]:
      np_image = np.frombuffer(frame[0], dtype=np.uint8)
      np_image = np_image.reshape(frame[1][1], frame[1][2], 3)
      frame = [frame[1][0], np_image] + frame[1][3:]
    else:
      frame = None  
    return(frame)

        
