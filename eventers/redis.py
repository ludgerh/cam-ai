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

  def push_to_webm(self, idx, value):
    self.rpush('cam-ai.eventers.webm_list:' + str(idx), value)
  
  def pop_from_webm(self, idx):
    if self.exists('cam-ai.eventers.webm_list:' + str(idx)):
      return(self.lpop('cam-ai.eventers.webm_list:' + str(idx)))
    else:
      return(None)  
    
my_redis = new_redis()      
