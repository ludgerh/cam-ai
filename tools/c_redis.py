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


import json
from datetime import datetime
from redis import Redis
from redis.exceptions import ConnectionError
from time import time, sleep

def reduce(value):
  if value and type(value) == bytes and len(value) > 20:
    return('len:', len(value))
  else:
    return(value)

class saferedis(Redis):
  def __init__(self):
    self.debug = False
    self.start_ts = time()
    super().__init__(health_check_interval=30)
    
  def get(self, key):
    for _ in range(10):  
      try:  
        result = super().get(key)
        if self.debug:
          print(round(time() - self.start_ts, 5), 'GET', key, reduce(result))
        return(result)
        break
      except ConnectionError:
        sleep(1.0)
    
  def set(self, key, value):
    if self.debug:
      print(round(time() - self.start_ts, 5), 'SET', key, reduce(value))
    for _ in range(10):  
      try:  
        super().set(key, value)
        break
      except ConnectionError:
        sleep(1.0)
    
  def incr(self, key):
    if self.debug:
      print(round(time() - self.start_ts, 5), 'INCR', key)
    super().incr(key)
    
  def decr(self, key):
    if self.debug:
      print(round(time() - self.start_ts, 5), 'DECR', key)
    super().decr(key)
    
  def delete(self, key):
    if self.debug:
      print(round(time() - self.start_ts, 5), 'DELETE', key)
    super().delete(key)
    
  def pubsub(self, *args, **kwargs):
    if self.debug:
      print(round(time() - self.start_ts, 5), 'PUBSUB', args, kwargs)
    return(super().pubsub(*args, **kwargs))

  def exists(self, *args, **kwargs):
    while True:
      try:
        if self.debug:
          result = super().exists(*args, **kwargs)
          print(round(time() - self.start_ts, 5), 'EXISTS', args, kwargs)
          return(result)
        else:  
          return(super().exists(*args, *kwargs))
        break
      except (ConnectionResetError, ConnectionError):
        now = datetime.now()
        print (now.strftime("%Y-%m-%d %H:%M:%S")+': Redis connection error from call of exists()') 
        sleep(1.0)  
    
  def rpop(self, key):
    if self.debug:
      result = super().rpop(key)
      print(round(time() - self.start_ts, 5), 'RPOP', key, reduce(result))
      return(result)
    else:  
      return(super().rpop(key))  
    
  def lpush(self, key, value):
    if self.debug:
      print(round(time() - self.start_ts, 5), 'LPUSH', key, reduce(value))
    super().lpush(key, value)   
    
  def publish(self, key, value):
    if self.debug:
      print(round(time() - self.start_ts, 5), 'PUBLISH', key, reduce(value))
    super().publish(key, value)   
    
  def llen(self, key):
    if self.debug:
      result = super().llen(key)
      print(round(time() - self.start_ts, 5), 'LLEN', key, reduce(result))
      return(result)
    else:  
      return(super().llen(key))
      
my_redis = saferedis()      
