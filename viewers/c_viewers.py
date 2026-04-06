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

import cv2 as cv
import asyncio
import struct
from threading import Event
from multiprocessing import Lock as p_lock
from time import time
from autobahn.exception import Disconnected
from globals.c_globals import viewables
from tools.c_tools import c_convert, c_buffer, add_view_count, take_view_count
from startup.redis import my_redis as startup_redis
from streams.redis import my_redis as streams_redis
from drawpad.drawpad import drawpad

#from threading import enumerate

class c_viewer():

  def __init__(self, type, idx, logger):
    self.logger = logger
    self.type = type
    self.id = idx
    self.xy_dim = (-1, -1)
    self.inqueue = c_buffer(
      block_put = False, 
      block_get = False, 
      call = self.callback,
      #debug = '*** Viewer: ' + self.type + str(self.id),
    )
    self.dbline = viewables[self.id]['stream'].dbline
    self.my_item = None
    #self.inqueue.display_qinfo('Init 1: ')
    self.client_dict_lock = p_lock()
    self.client_dict = {}
    self.event_loop = None #see consumers
    if self.type == 'E':
      self.drawpad = None
    else:  
      self.drawpad = drawpad(self, self.logger)
    self.framebuffer = None 
          
  async def onf(self, client_nr):
    import traceback
    try:
      if self.my_item is None:
        self.my_item = viewables[self.id][self.type]
      if not self.client_dict[client_nr]['busy'].is_set():
        self.client_dict[client_nr]['busy'].set()
        self.client_dict[client_nr]['lat_ts'] = time()
        ts = time()
        frame = (await self.inqueue.get())[1]
        if self.type in {'D', 'E'}:
          if self.type == 'D':  
            scaledown = self.my_item.shared_mem.read_1_meta('scaledown')
          else: #'E'
            scaledown = 1 
          outx = (self.my_item.shared_mem.read_1_meta('aoi_xdim') // scaledown)
          outy = (self.my_item.shared_mem.read_1_meta('aoi_ydim') // scaledown)
          if (self.client_dict[client_nr]['outx'] != outx 
              or self.client_dict[client_nr]['outy'] != outy):
            self.client_dict[client_nr]['outx'] = outx
            self.client_dict[client_nr]['x_scaling'] = (
              self.my_item.shared_mem.read_1_meta('aoi_xdim') 
                / self.client_dict[client_nr]['x_canvas']
                / scaledown
            )
            self.client_dict[client_nr]['outy'] = outy
            self.client_dict[client_nr]['y_canvas'] = round(
              self.client_dict[client_nr]['x_canvas'] * outy / outx
            )
            self.client_dict[client_nr]['y_scaling'] = (
              self.my_item.shared_mem.read_1_meta('aoi_ydim') 
                / self.client_dict[client_nr]['y_canvas']
                / scaledown
            )
            if self.type == 'D':  
              self.my_item.viewer.drawpad.set_xy((outx, outy)) 
              await self.my_item.viewer.drawpad.aload_ringlist()
              self.my_item.viewer.drawpad.make_screen()
              self.my_item.viewer.drawpad.mask_from_polygons()
        if self.type in {'C', 'D'}:
          if (self.drawpad.show_mask 
              and (self.drawpad.mask is not None)):
            if self.type == 'D' and not self.drawpad.edit_active:
              frame = cv.addWeighted(frame, 1, (255 - self.drawpad.mask), 0.3, 0)
            else:
              frame = cv.addWeighted(frame, 1, (255 - self.drawpad.mask), -0.3, 0)
          if self.drawpad.edit_active and self.drawpad.ringlist.len():
            if self.drawpad.whitemarks:
              frame = cv.addWeighted(frame, 1, 
                (255 - self.drawpad.screen), 1, 0)
            else:
              frame = cv.addWeighted(frame, 1, 
                (255 - self.drawpad.screen), -1.0, 0)
        if self.type == 'C' and self.drawpad.edit_active:
          rl = self.drawpad.ringlist
          if rl.rings and (
              rl.min_x > 0
              or rl.max_x < self.dbline.cam_xres - 1
              or rl.min_y > 0
              or rl.max_y < self.dbline.cam_yres - 1):
            cv.rectangle(
              frame, 
              (rl.min_x, rl.min_y),
              (rl.max_x, rl.max_y), 
              (255, 255, 0),
              4,
            ) 
        if self.client_dict[client_nr]['do_compress']:
          to = 3 #jpg
        else:
          to = 2 #bmp   
        frame = c_convert(frame, typein=1, typeout=to, 
          xout=self.client_dict[client_nr]['outx'])
        if not startup_redis.get_running() or streams_redis.get_killing_stream(self.id):  
          return()  
        indicator = struct.pack(
          '<4I', 
          self.client_dict[client_nr]['idx'], 
          self.client_dict[client_nr]['count'], 
          self.client_dict[client_nr]['x_canvas'],
          self.client_dict[client_nr]['y_canvas'], 
        )
        try: 
          #await self.client_dict[client_nr]['socket'].send(bytes_data = (
          #  self.client_dict[client_nr]['index'].encode()+frame
          #+))
          await self.client_dict[client_nr]['socket'].send(bytes_data = (
            self.client_dict[client_nr]['type']
              + indicator
              + frame
          )) 
        except Disconnected:
          self.logger.warning('*** Could not send Frame, socket closed...') 
    except Exception as e:
      print(e)
      traceback.print_exc()

  async def callback(self):  
    with self.client_dict_lock: 
      for item in self.client_dict:
        await self.onf(item)

  def push_to_onf(self, 
      outx = -1, 
      outy = -1, 
      x_canvas = -1, 
      y_canvas = -1, 
      x_scaling = -1.0,
      y_scaling = -1.0,
      do_compress = None, 
      websocket = None, 
    ):
    add_view_count(self.type, self.id)
    count = 0
    with self.client_dict_lock:
      while count in self.client_dict:
        count += 1
      client_info = {
        'index' : self.type + str(self.id).zfill(6) + str(count).zfill(6), #raus
        'type' : self.type.encode(),
        'idx' : self.id,
        'count' : count,
        'busy' : Event(),
        'outx' : outx,
        'outy' : outy,
        'x_canvas' : x_canvas,
        'y_canvas' : y_canvas,
        'x_scaling' : x_scaling,
        'y_scaling' : y_scaling,
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
      self.client_dict[client_nr]['lat_arr'].append(
        time() - self.client_dict[client_nr]['lat_ts']
      )
      if len(self.client_dict[client_nr]['lat_arr']) >= 10:
        #print('Latency:', self.parent.type, self.parent.id, mean(self.client_dict[client_nr]['lat_arr']))
        self.client_dict[client_nr]['lat_arr'] = []
    self.client_dict[client_nr]['busy'].clear()   

  def stop(self):
    self.inqueue.stop()
#    for thread in enumerate(): 
#      print(thread)

