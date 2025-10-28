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

class redis(saferedis):
  
  queue_stringbase = 'cam-ai.trainers.queue:'
  frames_stringbase = 'cam-ai.trainers.frames:'
  predict_stringbase = 'cam-ai.trainers.predict:'
  predict_started_stringbase = 'cam-ai.trainers.predict_started:'

  def set_trainerqueue(self, idx, value):
    self.set(self.queue_stringbase + str(idx)+':', str(json.dumps(value)))
    
  def get_trainerqueue(self, idx):
    result = self.get(self.queue_stringbase + str(idx)+':')
    if result:
      return(json.loads(result))
    else:
      return(None) 

  def set_last_frame(self, idx, value):
    self.set(self.frames_stringbase + str(idx)+':', value)
    
  def get_last_frame(self, idx):
    result = self.get(self.frames_stringbase + str(idx)+':')
    if result:
      return(int(result))
    else:
      return(0) 
      
  def get_predict_proc_active(self, idx): 
    result = self.get(self.predict_stringbase + str(idx)+':')
    if result:
      return(int(result))
    else:
      return(False)
      
  def set_predict_proc_active(self, idx, value): 
    if bool(value):
      self.set(self.predict_stringbase + str(idx)+':', 1)
    else:  
      self.set(self.predict_stringbase + str(idx)+':', 0) 
      
  def get_predict_proc_started(self, idx): 
    result = self.get(self.predict_started_stringbase + str(idx)+':')
    if result:
      return(int(result))
    else:
      return(False)
      
  def set_predict_proc_started(self, idx, value): 
    if bool(value):
      self.set(self.predict_started_stringbase + str(idx)+':', 1)
    else:  
      self.set(self.predict_started_stringbase + str(idx)+':', 0) 

      
my_redis = redis()      
