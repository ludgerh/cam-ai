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
import asyncio
#asyncio.get_event_loop().set_debug(True)
import numpy as np
from time import time
from threading import Lock as t_lock
from traceback import format_exc
from collections import deque
from multiprocessing import shared_memory as sm, Queue as mp_queue, Lock as p_lock, queues
from queue import Empty, Full, Queue as mt_queue
from copy import deepcopy
import pickle

"""
struct = coded list of transferred data blocks:
  O --> Python object
  L --> Large Python Object, going through shared memory
  B --> Bytes, variable length
  N --> Numpy array
  
m_proc: Use multiprocessing queues (default = True)
q_len: Length of data queue (default = 1), None: no queue (only if not m_proc)
block_put: Block put() until the previous data was read (default = True)
block_get: Block get() until new data (default = True)
put_timeout: Return after x seconds if blocked (default = None)
multi_in: More then one process as source, number of the input item element providing
  the index for sorting in (default = None)
call: Callback on the get side (default = None)
debug: Debug level (default = 0 (no debug output))
"""

PUT_STORAGE_ITEM = { 
  'max_size': -1, 
  'last_size': -1, 
  'shape': (), 
  'dtype': 0, 
  'shm': None,
}

GET_STORAGE_ITEM = {
  'last_size': -1, 
  'shape': (), 
  'dtype': 0, 
  'shm': None, 
  'name': '',
}

def debug_display(input):
  if isinstance(input, str):
    result = input
  elif input is None:
    result = str(input) 
  else: 
    result = []
    for item in input:
      if isinstance(item, np.ndarray): 
        result.append(('Numpy-Array:', item.shape))
      elif  isinstance(item, bytes):
        result.append(('Bytes:', len(item)))
      else:
        result.append(item)  
  return(result)
  
def count_sm(struct):
  return(struct.count('L') + struct.count('B') + struct.count('N'))

class l_buffer():
  def __init__(self, struct, m_proc = True, q_len = 1, block_put = True, 
      block_get = True, put_timeout = None, multi_in = None, call = None, 
      brake_time = 0.01, debug = 0):   
    self.struct = struct
    self.m_proc = m_proc
    self.q_len = q_len
    self.block_put = block_put
    self.block_get = block_get
    self.put_timeout = put_timeout
    self.multi_in = multi_in
    self.call = call
    self.brake_time = brake_time
    self.debug = debug  
    self.new_data = False
    if self.m_proc:
      self.data_queue = mp_queue(maxsize = self.q_len)
      #self.put_storage = [deepcopy(PUT_STORAGE_ITEM) for _ in self.struct]
      self.put_struct = {}
      self.put_storage = {}
      self.get_struct = {}
      self.get_storage = {}
      self.put_count = 0
      self.shm_deque = deque()
    else:
      if self.q_len is not None:
        self.data_queue = mt_queue(maxsize = self.q_len)
    if self.q_len is not None:
      self.data_loop_task = None
    self.multi_get_lock = p_lock()  
    self.multi_put_lock = p_lock()  
    self.do_run = True
    if self.block_put:
      self.shelf = False
    else:
      self.shelf = None 
    if not self.m_proc:
      self.lock = t_lock()
    
  def display_qinfo(self, info : 'Queue_Info: '): 
    if self.debug and self.m_proc:
      print(info + f'{os.getpid()} is using queue with ID {self.data_queue._reader.fileno()} {self.data_queue._writer.fileno()}')
    
  async def put_to_shelf(self, data): 
    
    while self.do_run:
      self.lock.acquire()
      if not self.block_put or self.shelf is False: 
        self.shelf = data
        self.lock.release()
        self.new_data = True
        if data is not None and data != 'stop' and self.call is not None:
          await self.call()  
        return()  
      else:
        self.lock.release()
        await asyncio.sleep(self.brake_time) 
    
  async def data_loop_runner(self):
    while self.do_run:
      try:
        data_in = self.data_queue.get(False)
        if self.debug:
          print(self.debug, '+++ Loop', debug_display(data_in)) 
        if data_in == 'stop' or data_in is None:
          data_out = data_in
        else:  
          data_out = [] 
          if self.q_len is not None:
            if self.m_proc:
              if self.multi_in is None:
                storage_idx = 0
              else:  
                storage_idx = data_in[self.multi_in][1]
              if storage_idx not in self.get_struct:
                self.get_struct[storage_idx] = self.struct
                self.get_storage[storage_idx] = [
                  deepcopy(GET_STORAGE_ITEM) for _ in self.struct
                ]  
            while len(data_in) > len(self.get_struct[storage_idx]):
              self.get_struct[storage_idx] += self.get_struct[storage_idx][-1]
              if self.m_proc:
                self.get_storage[storage_idx].append(deepcopy(GET_STORAGE_ITEM))
          for item in data_in:  
            i, data = item
            if not self.m_proc or self.get_struct[storage_idx][i] == 'O':
              data_out.append(data)
            else:
              storage = self.get_storage[storage_idx][i]
              if 'len' in data:
                storage['last_size'] = data['len']
              if 'name' in data:
                if data['name'] != storage['name']:
                  storage['shm'] = sm.SharedMemory(name=data['name'])
                  storage['name'] = data['name']
              if self.get_struct[storage_idx][i] == 'N':
                if 'shape' in data:
                  storage['shape'] = data['shape']
                if 'dtype' in data:
                  storage['dtype'] = data['dtype']
              in_bytes = storage['shm'].buf[1:storage['last_size'] + 1].tobytes()
              storage['shm'].buf[0] = 0
              if self.get_struct[storage_idx][i] == 'L':
                data_out.append(pickle.loads(in_bytes))
              elif self.get_struct[storage_idx][i] == 'B':
                data_out.append(in_bytes)
              elif self.get_struct[storage_idx][i] == 'N':
                data_out.append(np.ndarray(
                  storage['shape'], 
                  dtype=storage['dtype'], 
                  buffer=in_bytes,
                )) 
      except Empty:
        await asyncio.sleep(self.brake_time) 
        data_out = ''  
      if data_out: 
        await self.put_to_shelf(data_out) 
        if self.debug:
          print(self.debug, '--- Loop:', debug_display(data_out)) 
        
  async def multi_put(self, data): #not tested
    i = 0
    part = []
    with self.multi_put_lock:
      for item in data:
        part.append(data[i])
        i += 1
        if not i % len(self.struct) or i == len(data):
          await self.put(part) 
          part = []
      await self.put('stop')
    
  async def put(self, data):
    if self.debug:
      print(self.debug, '+++ Put', debug_display(data)) 
    if self.q_len is None: 
      if self.put_timeout:
        ts = time()
      while self.do_run:
        with self.lock:
          if not self.block_put or self.shelf is False: 
            if data != 'stop':
              data = enumerate(data) 
            self.shelf = data
            self.new_data = True
            return()
          else:
            if self.put_timeout and time() < ts + self.put_timeout:
              self.shelf = None
              return()
        await asyncio.sleep(self.brake_time) 
    if data == 'stop':
      try:
        await asyncio.to_thread(
          self.data_queue.put, 
          'stop', 
        )
      except Empty:
        raise Empty
      except Full:
        raise Full
      if self.debug:
        print(self.debug, '--- Put:', debug_display(data)) 
      return()
    if self.q_len is not None:
      if self.m_proc:
        if self.multi_in is None:
          storage_idx = 0
        else:  
          storage_idx = data[self.multi_in]
        if storage_idx not in self.put_struct:
          self.put_struct[storage_idx] = self.struct
          self.put_storage[storage_idx] = [
            deepcopy(PUT_STORAGE_ITEM) for _ in self.struct
          ]  
    while len(data) > len(self.put_struct[storage_idx]):
      self.put_struct[storage_idx] += self.put_struct[storage_idx][-1]
      if self.m_proc:
        self.put_storage[storage_idx].append(deepcopy(PUT_STORAGE_ITEM))
    data_for_send = []
    while self.shm_deque:
      age = self.put_count - self.shm_deque[0][0]
      if age < 0:
        age += 0xFFFF
      if age > self.q_len + 2:
        self.shm_deque.popleft()
      else:
        break  
    for i, item in enumerate(data):
      if not self.m_proc or  self.put_struct[storage_idx][i] == 'O':
        processed_item = item
      else:
        if self.put_struct[storage_idx][i] == 'L':
          data_bytes = pickle.dumps(item)
        elif self.put_struct[storage_idx][i] == 'B':
          data_bytes = item 
        elif self.put_struct[storage_idx][i] == 'N':
          data_bytes = item.tobytes()  
        data_length = len(data_bytes)
        storage = self.put_storage[storage_idx][i]
        processed_item = {}
        if self.put_struct[storage_idx][i] == 'N' and (item.shape != storage['shape'] 
            or item.dtype != storage['dtype']):
          processed_item.update({'shape': item.shape, 'dtype': item.dtype})
          storage.update({'shape': item.shape, 'dtype': item.dtype})
        if data_length != storage['last_size']:
          processed_item['len'] = data_length
          storage['last_size'] = data_length
          if data_length > storage['max_size']:
            storage['shm'] = sm.SharedMemory(create=True, size=data_length + 1)
            storage['shm'].buf[0] = 0 # free
            self.shm_deque.append((self.put_count, storage['shm']))
            processed_item['name'] = storage['shm'].name
            storage['max_size'] = data_length
        while storage['shm'].buf is None or storage['shm'].buf[0] == 1:
          await asyncio.sleep(0.01)
        storage['shm'].buf[0] = 1 # busy
        storage['shm'].buf[1:data_length + 1] = data_bytes
      data_for_send.append((i, processed_item))
    if self.m_proc:  
      if self.put_count < 0xFFFF:
        self.put_count += 1
      else:
        self.put_count = 0     
    try:  
      await asyncio.to_thread(
        self.data_queue.put, 
        data_for_send, 
        True, 
        self.put_timeout,
      )   
    except Empty:
      raise Empty
    except Full:
      raise Full
    except asyncio.exceptions.CancelledError:
      pass  
    if self.debug:
      print(self.debug, '--- Put:', debug_display(data_for_send)) 
      
  def start_data_loop(self):   
    if self.q_len is not None and self.data_loop_task is None:
      if self.m_proc:
        self.lock = t_lock()
      self.data_loop_task = asyncio.create_task(
        self.data_loop_runner(), 
        name = str(self.debug) + 'l_buffer_data_loop',
      ) 
      
  async def multi_get(self): #not tested
    result = []
    with self.multi_get_lock:
      while True:
        if (item := (await self.get())) == 'stop':
          return(result)
        else:
          result.extend(item)      

  async def get(self, timeout = None):
    if self.debug:
      print(self.debug, '+++ Get:')
    self.start_data_loop()
    if timeout:
      _get_ts = time()
    while self.do_run:
      with self.lock:
        if self.shelf is not False and (not self.block_get or self.new_data): 
          data_in = self.shelf  
          self.new_data = False
          if self.block_put: 
            self.shelf = False
          break
      if timeout and time() - _get_ts >= timeout:
        data_in = None
        break
      await asyncio.sleep(self.brake_time)
    if not self.do_run:
      return(None)
    if self.debug:
      print(self.debug, '--- Get:', debug_display(data_in))
    return(data_in)
      
  async def empty(self): #might cause problems if block_put is False
    with self.lock:
      shelf_temp = self.shelf
    if self.q_len is None: 
      return(shelf_temp is not False)
    else:
      return(await asyncio.to_thread(self.data_queue.empty) and shelf_temp is not False)  
      
  async def stop(self, mode = 'X'): 
    if self.q_len is None:
      return()  
    self.do_run = False  
    if mode == 'P':
      if self.m_proc:
        while not self.data_queue.empty():
          await asyncio.sleep(self.brake_time) 
        for item in self.shm_deque:
          item[1].close()
          item[1].unlink()
    else:   
      self.data_queue = None
      if self.data_loop_task is not None:
        self.data_loop_task.cancel()
      
