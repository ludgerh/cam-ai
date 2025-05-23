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

  def set_running(self, value):
    self.set('cam-ai.startup.running:', str(value))
  
  def get_running(self):
    if (result := self.get('cam-ai.startup.running:')):
      return(result.lower() == b'true')
    else:
      return(False) 
    
  def set_start_worker_busy(self, value):
    self.set('cam-ai.startup.worker_busy:', str(value)) 
    
  def set_start_stream_busy(self, value):
    self.set('cam-ai.startup.stream_busy:', str(value)) 
    
  def set_start_trainer_busy(self, value):
    self.set('cam-ai.startup.trainer_busy:', str(value)) 
    
  def set_watch_status(self, value): #0 : finish, 1 : wait, 2 : restart
    self.set('cam-ai.startup.watch_status:', value)   
    
  def get_shutdown_command(self): #0 : nothing, 1 : stop CAM-AI, 2 : restart CAM-AI
    if (result := self.get('cam-ai.startup.shutdown:')) is None:
      return(0)
    else:  
      return(int(result)) 
    
  def set_shutdown_command(self, value): #0 : nothing, 1 : stop CAM-AI, 2 : restart CAM-AI
    self.set('cam-ai.startup.shutdown:', value) 
    
  def get_start_worker_busy(self):
    if (result := self.get('cam-ai.startup.worker_busy')) is None:
      return(0)
    else:  
      return(int(result))  
    
  def get_start_stream_busy(self):
    if (result := self.get('cam-ai.startup.stream_busy:')) is None:
      return(0)
    else:  
      return(int(result))  
    
  def get_start_trainer_busy(self):
    if (result := self.get('cam-ai.startup.trainer_busy:')) is None:
      return(0)
    else:  
      return(int(result))  
    
  def get_watch_status(self):  #0 : finish, 1 : wait, 2 : restart
    while (result := self.get('cam-ai.startup.watch_status:')) is None:
      sleep(1.0)  
    return(int(result))  
      
my_redis = new_redis()   
