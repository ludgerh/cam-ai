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

class trainers_redis(saferedis):

  def set_trainerqueue(self, idx, value):
    #print('+++++ setting', idx, value)
    self.set('trainers.queue.'+str(idx)+':', str(json.dumps(value)))
    
  def get_trainerqueue(self, idx):
    result = self.get('trainers.queue.'+str(idx)+':')
    if result:
      #print('----- getting', idx, json.loads(result))
      return(json.loads(result))
    else:
      return(None) 
      
my_redis = trainers_redis()      
