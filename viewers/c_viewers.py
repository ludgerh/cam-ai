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

import cv2 as cv
import asyncio
from threading import Event
from multiprocessing import Lock as p_lock
from time import time
from globals.c_globals import viewables
from tools.c_tools import c_convert, c_buffer, add_view_count, take_view_count
from startup.redis import my_redis as startup_redis
from streams.redis import my_redis as streams_redis
from drawpad.drawpad import drawpad

#from threading import enumerate

class c_viewer():

  def __init__(self, type, idx, xdim, ydim, scaledown, logger):
    self.logger = logger
    self.type = type
    self.id = idx
    self.xdim = xdim
    self.ydim = ydim
    self.scaledown = scaledown
    self.inqueue = c_buffer(
      block_put = False, 
      block_get = False, 
      call = self.callback,
      #debug = '*** Viewer: ' + self.type + str(self.id),
    )
    #self.inqueue.display_qinfo('Init 1: ')
    self.client_dict_lock = p_lock()
    self.client_dict = {}
    self.event_loop = None #see consumers
    if self.type == 'E':
      self.drawpad = None
    else:  
      self.drawpad = drawpad(self, self.logger)
      self.drawpad.mtype = self.type
      self.drawpad.myid = self.id
    self.framebuffer = None 
          
  async def onf(self, client_nr):
    if not self.client_dict[client_nr]['busy'].is_set():
      self.client_dict[client_nr]['busy'].set()
      self.client_dict[client_nr]['lat_ts'] = time()
      ts = time()
      frame = (await self.inqueue.get())[1]
      if self.type == 'D':
        if (self.drawpad.show_mask 
            and (self.drawpad.mask is not None)):
          frame = cv.addWeighted(frame, 1, 
            (255-self.drawpad.mask), 0.3, 0)
      elif self.type == 'C':
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
        to = 3 #jpg
      else:
        to = 2 #bmp 
      frame = c_convert(frame, typein=1, typeout=to, 
        xout=self.client_dict[client_nr]['outx'])
      if not startup_redis.get_running() or streams_redis.get_killing_stream(self.id):  
        return()  
      try:
        await self.client_dict[client_nr]['socket'].send(bytes_data = (
          self.client_dict[client_nr]['index'].encode()+frame
        ))
      except Disconnected:
        logger.warning('*** Could not send Frame, socket closed...')

  async def callback(self):  
    with self.client_dict_lock: 
      for item in self.client_dict:
        await self.onf(item)
        

  def push_to_onf(self, outx, do_compress, websocket):
    add_view_count(self.type, self.id)
    count = 0
    with self.client_dict_lock:
      while count in self.client_dict:
        count += 1
      client_info = {
        'index' : self.type + str(self.id).zfill(6) + str(count).zfill(6),
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
    take_view_count(self.type, self.id)
      
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

