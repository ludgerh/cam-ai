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
  
  stringbase = 'cam-ai.tf_workers.'
  
  def set_buf_size(self, idx, value):
    self.set(self.stringbase + 'buf_size:' + str(idx) + ':', str(value))
    
  def get_buf_size(self, idx):  
    result = self.get(self.stringbase + 'buf_size:'+str(idx)+':')
    if result is None:
      return(0)   
    return(int(result))
  
  def set_buf_size_10(self, idx, value):
    self.set(self.stringbase + 'buf_size_10:' + str(idx) + ':', str(value))
    
  def get_buf_size_10(self, idx):   
    result = self.get(self.stringbase + 'buf_size_10:'+str(idx)+':')
    if result is None:
      return(0.0)   
    return(float(result))
  
  def set_block_size(self, idx, value):
    self.set(self.stringbase + 'block_size:' + str(idx) + ':', str(value))
    
  def get_block_size(self, idx):   
    result = self.get(self.stringbase + 'block_size:'+str(idx)+':')
    if result is None:
      return(0)   
    return(int(result))
  
  def set_block_size_10(self, idx, value):
    self.set(self.stringbase + 'block_size_10:' + str(idx) + ':', str(value))
    
  def get_block_size_10(self, idx):    
    result = self.get(self.stringbase + 'block_size_10:'+str(idx)+':')
    if result is None:
      return(0.0)   
    return(float(result))
  
  def set_proc_time(self, idx, value):
    self.set(self.stringbase + 'proc_time:' + str(idx) + ':', str(value))
    
  def get_proc_time(self, idx):    
    result = self.get(self.stringbase + 'proc_time:'+str(idx)+':')
    if result is None:
      return(0.0)   
    return(float(result)) 
  
  def set_proc_time_10(self, idx, value):
    self.set(self.stringbase + 'proc_time_10:' + str(idx) + ':', str(value))
    
  def get_proc_time_10(self, idx):   
    result = self.get(self.stringbase + 'proc_time_10:'+str(idx)+':')
    if result is None:
      return(0.0)   
    return(float(result)) 
      
my_redis = new_redis()      
