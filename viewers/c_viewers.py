# viewers/c_viewers.py
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
import traceback
from threading import Event
from time import monotonic
from autobahn.exception import Disconnected
from globals.c_globals import viewables
from tools.c_tools import c_convert, c_buffer, add_view_count, take_view_count
from tools.l_break import a_break_type, BR_SHORT
from startup.redis import my_redis as startup_redis
from streams.redis import my_redis as streams_redis
from drawpad.drawpad import drawpad
#from threading import enumerate
# how long to wait for a client ack before assuming the frame was lost on the
# wire (or the ack got stuck) and freeing the busy slot, so the stream resumes
# instead of livelocking forever. comfortably above the 1s off-screen ack delay.
ACK_TIMEOUT = 3.0

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
    self.client_dict = {}
    if self.type == 'E':
      self.drawpad = None
    else:  
      self.drawpad = drawpad(self, self.logger)
    self.framebuffer = None
    self._next_client_nr = 0
    self.x_canvas_max = 0
          
  async def onf(self, client_nr):
    client = None
    i_set_busy = False  # did THIS call acquire the busy flag?
    send_succeeded = False
    try:
      if self.my_item is None:
        self.my_item = viewables[self.id][self.type]
      client = self.client_dict[client_nr]
      if not client['busy'].is_set():
        client['busy'].set()
        i_set_busy = True
        client['busy_set_at'] = monotonic()  # start the ack watchdog clock
        frame = (await self.inqueue.get())[1]
        if self.type in {'D', 'E'}:  
          xdim = self.my_item.shared_mem.read_1_meta('aoi_xdim')
          ydim = self.my_item.shared_mem.read_1_meta('aoi_ydim')
          if xdim != client['old_x'] or ydim != client['old_y']:
            client['old_x'] = xdim
            client['old_y'] = ydim 
            if self.type == 'D':  
              scaledown = self.my_item.shared_mem.read_1_meta('scaledown')
            else: #'E'
              scaledown = 1 
            client['y_canvas'] =  round(client['x_canvas'] * ydim / xdim)
            client['x_scaling'] = xdim / client['x_canvas'] / scaledown
            client['y_scaling'] = ydim / client['y_canvas'] / scaledown 
            client['outx'] = min(client['x_canvas'], xdim // scaledown)
            client['outy'] = min(client['y_canvas'], ydim // scaledown)
            if self.type == 'D':  
              self.my_item.viewer.drawpad.set_xy((xdim // scaledown, ydim // scaledown)) 
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
        if client['do_compress']:
          to = 3 #jpg
        else:
          to = 2 #bmp  
        frame = c_convert(frame, typein=1, typeout=to, xout=client['outx'])
        if not startup_redis.get_running() or streams_redis.get_killing_stream(self.id):  
          return()  
        indicator = struct.pack(
          '<4I', 
          client['idx'], 
          client['count'], 
          client['x_canvas'],
          client['y_canvas'], 
        )
        try: 
          await client['socket'].send(bytes_data = (client['type'] + indicator + frame))
          send_succeeded = True
        except Disconnected:
          pass
    except Exception as exc:
      # use self.logger (there is no module-level logger here);
      # this handler must never raise, or the data loop dies for good
      self.logger.warning(
        f'*** ONF {self.type}{self.id} could not send frame: {exc!r}',
        exc_info=True,
      ) 
    except Exception:
      # use self.logger (there is no module-level logger here);
      # this handler must never raise, or the data loop dies for good
      self.logger.warning(f'*** ONF {self.type}{self.id} could not send frame')
    finally:
      # only release if we acquired it here and the send did not go out
      if client is not None and i_set_busy and not send_succeeded and client['busy'].is_set():
        client['busy'].clear()
        client['busy_set_at'] = None
        
  async def callback(self):
    clients = list(self.client_dict.keys())
    served = False
    for item in clients:
      client = self.client_dict.get(item)
      if client is None:
        continue
      # ack watchdog: if a frame has been in-flight without an ack for longer
      # than ACK_TIMEOUT, assume it was lost (or the ack got stuck) and free the
      # slot. without this the client waits for an ack that never comes and the
      # whole stream livelocks.
      if (client['busy'].is_set()
          and client['busy_set_at'] is not None
          and (monotonic() - client['busy_set_at']) > ACK_TIMEOUT):
        if self.type == 'E' and self.id == 1:  
          self.logger.warning(
            f'*** ONF {self.type}{self.id} ack timeout after '
            f'{monotonic() - client["busy_set_at"]:.1f}s, freeing busy slot'
          )
        client['busy'].clear()
        client['busy_set_at'] = None
      if not client['busy'].is_set():
        served = True
        await self.onf(item)
    if not served:
      # all clients busy: this frame cannot be sent now. Yield, otherwise the
      # producer-driven loop never hands control back and the ack coroutine
      # (clear_busy) is starved -> livelock.
      await a_break_type(BR_SHORT)

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
    if self.my_item is None:
      self.my_item = viewables[self.id][self.type]
    add_view_count(self.type, self.id)
    count = self._next_client_nr
    self._next_client_nr += 1
    client_info = {
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
      'do_compress' : do_compress,
      'old_x' : -1,
      'old_y' : -1,
      'busy_set_at' : None,  # timestamp when busy was set, for the ack watchdog
    }
    client_info['busy'].set()
    self.client_dict[count] = client_info
    self.x_canvas_max = max(x_canvas, self.x_canvas_max)
    self.my_item.shared_mem.write_1_meta('x_canvas', self.x_canvas_max)
    return(count)

  def pop_from_onf(self, client_nr):
    del self.client_dict[client_nr]
    take_view_count(self.type, self.id)
    result = 0
    for item in self.client_dict.values():
      result = max(item['x_canvas'], result)
    self.x_canvas_max = result   
    self.my_item.shared_mem.write_1_meta('x_canvas', self.x_canvas_max)
      
  def clear_busy(self, client_nr):
    client = self.client_dict.get(client_nr)
    if client is not None:
      client['busy'].clear()
      client['busy_set_at'] = None  # ack arrived, stop the watchdog clock

  def stop(self):
    self.inqueue.stop()
#    for thread in enumerate(): 
#      print(thread)

