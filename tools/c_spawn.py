"""
Copyright (C) 2025 by the CAM-AI team, info@cam-ai.de
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

import django
django.setup()
import asyncio
from traceback import format_exc
from signal import signal, SIGINT
from multiprocessing import Process, SimpleQueue as s_queue
from l_buffer.l_buffer import l_buffer
from globals.c_globals import viewables, add_viewer
from streams.redis import my_redis as streams_redis
from viewers.c_viewers import c_viewer

def sigint_handler(signal = None, frame = None ):
  pass

class QueueUnknownKeyword(Exception):
  def __init__(self, keyword, message="Unknown keyword: "):
    self.message = message + keyword
    super().__init__(self.message)

class spawn_process(Process):
  def __init__(self, buffer_code = None):
    if buffer_code:
      self.use_buffer = True
      self.inqueue = l_buffer(
        buffer_code, 
        multi_in = 1, 
        #debug = 'TF-Worker-In:',
      )
    else:
      self.use_buffer = False
      self.inqueue = s_queue()
    super().__init__()

  def run(self):
    asyncio.run(self.async_runner())
        
  async def async_runner(self):
    signal(SIGINT, sigint_handler)
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(SIGINT, sigint_handler)
    asyncio.create_task(self.in_queue_thread(), name = 'in_queue_thread')
    self.do_run = True
        
  async def process_received(self, received):  
    result = False
    return(result)

  async def in_queue_thread(self):
    try:
      while self.do_run:
        if self.use_buffer:
          received = await self.inqueue.get()
        else:  
          received = await asyncio.to_thread(self.inqueue.get)
        if (received[0] == 'stop'): 
          self.do_run = False
          break 
        else:  
          if not await self.process_received(received):
            raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error('Error in process: ' + self.logname + ' (inqueue)')
      self.logger.error(format_exc())
  
  async def stop(self):
    if self.is_alive():
      self.do_run = False
      if self.use_buffer:
        await self.inqueue.put(('stop', 0, ))
      else:  
        self.inqueue.put(('stop',))
    
class viewable(spawn_process):
  def __init__(self, logger, ):
    if self.type == 'D':
      scaledown = self.scaledown
    else:
      scaledown = 1  
    add_viewer((my_viewer := c_viewer(
      self.type, 
      self.id, 
      self.dbline.cam_xres, 
      self.dbline.cam_yres, 
      scaledown,
      logger,
    )))
    self.viewer = my_viewer
    self.viewer_queue = my_viewer.inqueue
    streams_redis.zero_to_dev(self.type, self.id)
    streams_redis.fps_to_dev(self.type, self.id, 0.0)
    super().__init__()
  
  async def run_here(self): #Run on the original (=Main-) Process 
    #from streams.models import stream as dbstream
    #self.dbline = await dbstream.objects.aget(id = self.id)
    self.viewer.inqueue.display_qinfo(info = self.type + ' ' + str(self.id) +  ' Spawn: ')
    self.viewer.inqueue.start_data_loop()

  async def async_runner(self):
    from tools.c_tools import speedlimit, speedometer
    from streams.models import stream as dbstream
    self.dbline = await dbstream.objects.aget(id = self.id)
    if self.type in ['D', 'E']:
      if self.dbline.cam_virtual_fps:
        self.sl = speedlimit(period = 0.0)
      else:  
        if self.type == 'D':
          limit = self.dbline.det_fpslimit
        elif self.type == 'E':
          limit = self.dbline.eve_fpslimit  
        if limit:  
          self.sl = speedlimit(period = 1.0 / limit)
        else:  
          self.sl = speedlimit(period = 0.0)
    self.som = speedometer()
    await super().async_runner()   
    
