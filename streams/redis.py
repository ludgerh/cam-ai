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


import json
from tools.c_redis import saferedis

class new_redis(saferedis):
  
  stringbase = 'cam-ai.streams.'

  def set_killing_stream(self, idx, value):
    self.set(self.stringbase + 'killing:' + str(idx) + ':', str(value))
    
  def get_killing_stream(self, idx):
    if (result := self.get(self.stringbase + 'killing:' + str(idx) + ':')):
      return(result.lower() == b'true')
    else:
      return(False)  
      
  def zero_to_dev(self, type, idx):
    self.set(self.stringbase + 'viewcount:' + type + ':' + str(idx) + ':', 0)
    self.set(self.stringbase + 'recordcount:' + type + ':' + str(idx) + ':', 0)
    self.set(self.stringbase + 'datacount:' + type + ':' + str(idx) + ':', 0)
    
  def view_from_dev(self, type, idx):
    return(int(self.get(self.stringbase + 'viewcount:' + type + ':' + str(idx) + ':')))

  def record_from_dev(self, type, idx):
    return(int(self.get(self.stringbase + 'recordcount:' + type + ':' + str(idx) + ':')))

  def data_from_dev(self, type, idx):
    return(int(self.get(self.stringbase + 'datacount:' + type + ':' + str(idx) + ':')))

  def inc_view_dev(self, type, idx):
    self.incr(self.stringbase + 'viewcount:' + type + ':' + str(idx) + ':')

  def inc_record_dev(self, type, idx):
    self.incr(self.stringbase + 'recordcount:' + type + ':' + str(idx) + ':')

  def inc_data_dev(self, type, idx):
    self.incr(self.stringbase + 'datacount:' + type + ':' + str(idx) + ':')

  def dec_view_dev(self, type, idx):
    if self.view_from_dev(type, idx) > 0:
      self.decr(self.stringbase + 'viewcount:' + type + ':' + str(idx) + ':')

  def dec_record_dev(self, type, idx):
    if self.record_from_dev(type, idx) > 0:
      self.decr(self.stringbase + 'recordcount:' + type + ':' + str(idx) + ':')

  def dec_data_dev(self, type, idx):
    if self.data_from_dev(type, idx) > 0:
      self.decr(self.stringbase + 'datacount:' + type + ':' + str(idx) + ':')

  def set_view_dev(self, type, idx, value):
    self.set(self.stringbase + 'viewcount:' + type + ':' + str(idx) + ':', value)

  def set_record_dev(self, type, idx, value):
    self.set(self.stringbase + 'recordcount:' + type + ':' + str(idx) + ':', value)

  def set_data_dev(self, type, idx, value):
    self.set(self.stringbase + 'datacount:' + type + ':' + str(idx) + ':', value)

  def check_if_counts_zero(self, type, idx):
    result = self.get(self.stringbase + 'viewcount:' + type + ':' + str(idx) + ':')
    if result and int(result):
      return(False)
    result = self.get(self.stringbase + 'recordcount:' + type + ':' + str(idx) + ':')
    if result and int(result):
      return(False)
    result = self.get(self.stringbase + 'datacount:' + type + ':' + str(idx) + ':')
    if result and int(result):
      return(False)
    return(True)

  def fps_to_dev(self, type, idx, value):
    self.set(self.stringbase + 'fps:' + type + ':' + str(idx) + ':', str(value))

  def fps_from_dev(self, type, idx):
    return(float(self.get(self.stringbase + 'fps:' + type + ':' + str(idx) + ':')))

  def x_y_res_to_cam(self, idx, xres, yres):
    self.set(self.stringbase + 'xres:'+str(idx)+':', xres)
    self.set(self.stringbase + 'yres:'+str(idx)+':', yres)

  def x_y_res_from_cam(self, idx):
    x = int(self.get(self.stringbase + 'xres:'+str(idx)+':'))
    y = int(self.get(self.stringbase + 'yres:'+str(idx)+':'))
    return((x, y))
    
  def set_ptz(self, idx, value):
    self.set(self.stringbase + 'ptz:'+str(idx)+':', str(json.dumps(value)))
    
  def get_ptz_json(self, idx):
    return(self.get(self.stringbase + 'ptz:'+str(idx)+':'))  
    
  def get_ptz(self, idx):
    result = self.get_ptz_json(idx)
    if result:
      return(json.loads(result))
    else:
      return(None)  
    
  def set_ptz_pos(self, idx, value):
    self.set(self.stringbase + 'ptzpos:'+str(idx)+':', str(json.dumps(value)))
    
  def get_ptz_pos(self, idx):
    return(json.loads(self.get(self.stringbase + 'ptzpos:'+str(idx)+':')))  
    
  def set_virt_time(self, idx, value):  
    self.set(self.stringbase + 'virt_time:'+str(idx)+':', value) 
    
  def get_virt_time(self, idx):  
    return(float(self.get(self.stringbase + 'virt_time:'+str(idx)+':')))  
      
my_redis = new_redis()      
