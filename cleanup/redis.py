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
from tools.l_break import break_type, BR_MEDIUM

class new_redis(saferedis):
  def __init__(self):
    self.tag = 'cam-ai.cleanup:'
    super().__init__()
 
  def clean_redis(self, name, idx=0): 
    self.delete(self.tag + name + ':' + str(idx))
     
  def add_to_redis(self, name, idx, myvalue):
    self.set(self.tag + name + ':' + str(idx), myvalue)
     
  def get_from_redis(self, name, idx):
    mytag = self.tag + name + ':' + str(idx)
    while (not self.exists(mytag)):
      break_type(BR_MEDIUM)
    return(int(self.get(mytag)))
     
  def add_to_redis_queue(self, name, idx, myset):
    mytag = self.tag + name + ':' + str(idx)
    self.delete(mytag)
    for item in myset:
      self.lpush(mytag, item)
    
  def get_from_redis_queue(self, name, idx):
    mytag = self.tag + name + ':' + str(idx)
    result = []  
    if self.exists(mytag):
      while (rline := self.rpop(mytag)):
        result.append(rline) 
    return(result)  
    
  def len_from_redis_queue(self, name, idx):
    mytag = self.tag + name + ':' + str(idx)
    if self.exists(mytag):
      return(self.llen(mytag))  
    else:
      return(0)  
      
  def get_user_used_quota(self, idx): 
    result = self.get(self.tag + 'user_used_quota:' + ':' + str(idx))
    if result is None:
      return(0)
    else:
      return(int(result))  
      
  def set_user_used_quota(self, idx, value): 
    self.set(self.tag + 'user_used_quota:' + ':' + str(idx), value) 
    
my_redis = new_redis()      
