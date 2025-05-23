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
  
  stringbase = 'cam-ai.tools.zip_info:'

  def purge_zip_info(self, idx):
    if self.exists(self.stringbase + str(idx) + ':'):
      self.delete(self.stringbase + str(idx) + ':')
      
  def get_zip_info(self, idx):  
    result = self.get(self.stringbase + str(idx) + ':')  
    if result:
      self.delete(self.stringbase + str(idx) + ':')
    return(result)  
      
  def set_zip_info(self, idx, info):  
    self.set(self.stringbase + str(idx) + ':', info) 
    
  def get_totaldiscspace(self):
    result = self.get('cam-ai.tools.totaldiscspace:')
    if result is None:
      return(0)
    else:
      return(int(result))
      
  def set_totaldiscspace(self, value): 
    self.set('cam-ai.tools.totaldiscspace:', value)   
    
  def get_freediscspace(self):
    result = self.get('cam-ai.tools.freediscspace:')
    if result is None:
      return(0)
    else:
      return(int(result))
      
  def set_freediscspace(self, value): 
    self.set('cam-ai.tools.freediscspace:', value)   
    
  def get_useddiscspace(self):
    result = self.get('cam-ai.tools.useddiscspace:')
    if result is None:
      return(0)
    else:
      return(int(result))
      
  def set_useddiscspace(self, value): 
    self.set('cam-ai.tools.useddiscspace:', value)   
    
    
my_redis = new_redis()      
