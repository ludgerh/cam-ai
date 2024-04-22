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

import cv2 as cv
import asyncio
from statistics import mean
from threading import Lock, Event
from time import time
from l_buffer.l_buffer import c_buffer
from tools.c_tools import c_convert
from tools.c_redis import myredis
from drawpad.drawpad import drawpad

#from threading import enumerate

redis = myredis()

class c_viewer():

  def __init__(self, parent, logger):
    self.logger = logger
    self.parent = parent
    self.inqueue = c_buffer(call=self.callback)
    self.client_dict_lock = Lock()
    self.client_dict = {}
    self.event_loop = None #see consumers
    if self.parent.type in {'C', 'D'}:
      self.drawpad = drawpad(self, self.logger)
          
  async def onf(self, client_nr):  
    if not self.client_dict[client_nr]['busy'].is_set():
      self.client_dict[client_nr]['busy'].set()
      self.client_dict[client_nr]['lat_ts'] = time()
      ts = time()
      frame = self.inqueue.get()[1]
      if self.parent.type == 'D':
        if (self.drawpad.show_mask 
            and (self.drawpad.mask is not None)):
          frame = cv.addWeighted(frame, 1, 
            (255-self.drawpad.mask), 0.3, 0)
      elif self.parent.type == 'C':
        if (self.drawpad.show_mask 
            and (self.drawpad.mask is not None)):
          frame = cv.addWeighted(frame, 1, 
            (255-self.drawpad.mask), -0.3, 0)
        if self.drawpad.edit_active and self.drawpad.ringlist:
          if self.drawpad.whitemarks:
            frame = cv.addWeighted(frame, 1, 
              (255-self.drawpad.screen), 1, 0)
          else:
            frame = cv.addWeighted(frame, 1, 
              (255-self.drawpad.screen), -1.0, 0)
      if self.client_dict[client_nr]['do_compress']:
        to = 3
      else:
        to = 2         
      frame = c_convert(frame, typein=1, typeout=to, 
        xout=self.client_dict[client_nr]['outx'])
      if (int(redis.get('CAM-AI:KBInt')) 
          or int(redis.get('CAM-AI:KillStream:' + str(self.parent.id)))):
        return()  
      try:
        await self.client_dict[client_nr]['socket'].send(bytes_data = (
          self.client_dict[client_nr]['index'].encode()+frame
        ))
      except Disconnected:
        logger.warning('*** Could not send Frame, socket closed...')    

  def callback(self):   
    with self.client_dict_lock:
      for item in self.client_dict:
        self.onf(item)
        asyncio.run_coroutine_threadsafe(self.onf(item), self.event_loop)
        

  def push_to_onf(self, outx, do_compress, websocket):
    self.parent.add_view_count()
    count = 0
    with self.client_dict_lock:
      while count in self.client_dict:
        count += 1
      client_info = {
        'index' : self.parent.type + str(self.parent.id).zfill(6) + str(count).zfill(6),
        'busy' : Event(),
        'outx' : outx,
        'socket' : websocket,
        'lat_ts' : 0.0,
        'lat_arr' : [],
        'do_compress' : do_compress,
      }
      client_info['busy'].set()
      self.client_dict[count] = client_info
    return(count)

  def pop_from_onf(self, client_nr):
    with self.client_dict_lock:
      del self.client_dict[client_nr]
    self.parent.take_view_count()
      
  def clear_busy(self, client_nr):
    if self.client_dict[client_nr]['lat_ts']:
      self.client_dict[client_nr]['lat_arr'].append(time() - self.client_dict[client_nr]['lat_ts'])
      if len(self.client_dict[client_nr]['lat_arr']) >= 10:
        #print('Latency:', self.parent.type, self.parent.id, mean(self.client_dict[client_nr]['lat_arr']))
        self.client_dict[client_nr]['lat_arr'] = []
    self.client_dict[client_nr]['busy'].clear()   

  def stop(self):
    self.inqueue.stop()
#    for thread in enumerate(): 
#      print(thread)

