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
  
  stringbase = 'cam-ai.eventer.webm_queue:'

  def del_webm_queue(self, idx):
    self.delete(self.stringbase + str(idx) + ':')
    
  def webm_queue_exists(self, idx):  
    return(self.exists(self.stringbase + str(idx) + ':'))
    
  def webm_queue_qsize(self, idx):  
    return(self.llen(self.stringbase + str(idx) + ':'))
    
  def webm_queue_get(self, idx):  
    return(self.rpop(self.stringbase + str(idx) + ':').decode("utf-8"))
    
  def webm_queue_put(self, idx, data):  
    self.lpush(self.stringbase + str(idx) + ':', data)
  
my_redis = new_redis()      
