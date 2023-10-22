# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
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

import json
from datetime import datetime
from redis import Redis
from redis.exceptions import ConnectionError
from time import sleep

class saferedis(Redis):
  def __init(self):
    super().__init__(health_check_interval=30)

  def exists(self, *args, **kwargs):
    while True:
      try:
        return(super().exists(*args, *kwargs))
        break
      except (ConnectionResetError, ConnectionError):
        now = datetime.now()
        print (now.strftime("%Y-%m-%d %H:%M:%S")+': Redis connection error from call of exists()') 
        sleep(0.1)       

class myredis(saferedis):

  def zero_to_dev(self, type, idx):
    self.set(type+':'+str(idx)+':viewcount', 0)
    self.set(type+':'+str(idx)+':recordcount', 0)
    self.set(type+':'+str(idx)+':datacount', 0)

  def view_from_dev(self, type, idx):
    return(int(self.get(type+':'+str(idx)+':viewcount')))

  def record_from_dev(self, type, idx):
    return(int(self.get(type+':'+str(idx)+':recordcount')))

  def data_from_dev(self, type, idx):
    return(int(self.get(type+':'+str(idx)+':datacount')))

  def inc_view_dev(self, type, idx):
    self.incr(type+':'+str(idx)+':viewcount')

  def inc_record_dev(self, type, idx):
    self.incr(type+':'+str(idx)+':recordcount')

  def inc_data_dev(self, type, idx):
    self.incr(type+':'+str(idx)+':datacount')

  def dec_view_dev(self, type, idx):
    self.decr(type+':'+str(idx)+':viewcount')

  def dec_record_dev(self, type, idx):
    self.decr(type+':'+str(idx)+':recordcount')

  def dec_data_dev(self, type, idx):
    self.decr(type+':'+str(idx)+':datacount')

  def set_view_dev(self, type, idx, value):
    self.set(type+':'+str(idx)+':viewcount', value)

  def set_record_dev(self, type, idx, value):
    self.set(type+':'+str(idx)+':recordcount', value)

  def set_data_dev(self, type, idx, value):
    self.set(type+':'+str(idx)+':datacount', value)

  def check_if_counts_zero(self, type, idx):
    if int(self.get(type+':'+str(idx)+':viewcount')) > 0:
      return(False)
    if int(self.get(type+':'+str(idx)+':recordcount')) > 0:
      return(False)
    if int(self.get(type+':'+str(idx)+':datacount')) > 0:
      return(False)
    return(True)
    

  def x_y_res_to_cam(self, idx, xres, yres):
    self.set('C:'+str(idx)+':xres', xres)
    self.set('C:'+str(idx)+':yres', yres)

  def x_y_res_from_cam(self, idx):
    x = int(self.get('C:'+str(idx)+':xres'))
    y = int(self.get('C:'+str(idx)+':yres'))
    return((x, y))

  def name_to_stream(self, idx, name):
    self.set('ST:'+str(idx)+':name', name)

  def name_from_stream(self, idx):
    return(self.get('ST:'+str(idx)+':name'))

  def fps_to_dev(self, type, idx, value):
    self.set(type+':'+str(idx)+':fps', str(value))

  def fps_from_dev(self, type, idx):
    return(float(self.get(type+':'+str(idx)+':fps')))
    
  def set_start_worker_busy(self, value):
    self.set('start_worker_busy', str(value)) 
    
  def set_start_stream_busy(self, value):
    self.set('start_stream_busy', str(value)) 
    
  def set_start_trainer_busy(self, value):
    self.set('start_trainer_busy', str(value)) 
    
  def get_start_worker_busy(self):
    return(int(self.get('start_worker_busy')))  
    
  def get_start_stream_busy(self):
    return(int(self.get('start_stream_busy'))) 
    
  def get_start_trainer_busy(self):
    return(int(self.get('start_trainer_busy'))) 
    
  def set_ptz(self, idx, value):
    self.set('C:'+str(idx)+':ptz', str(json.dumps(value)))
    
  def get_ptz_json(self, idx):
    return(self.get('C:'+str(idx)+':ptz'))  
    
  def get_ptz(self, idx):
    return(json.loads(self.get_ptz_json(idx)))
    
  def set_ptz_pos(self, idx, value):
    self.set('C:'+str(idx)+':ptzpos', str(json.dumps(value)))
    
  def get_ptz_pos(self, idx):
    return(json.loads(self.get('C:'+str(idx)+':ptzpos')))  
