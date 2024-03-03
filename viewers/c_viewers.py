"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

from threading import Lock
from l_buffer.l_buffer import l_buffer
from drawpad.drawpad import drawpad

#from threading import enumerate

class c_viewer():

  def __init__(self, parent, logger):
    self.logger = logger
    self.parent = parent
    self.inqueue = l_buffer(1, call=self.callback)
    self.onf_dict_lock = Lock()
    self.onf_dict = {}
    if self.parent.type in {'C', 'D'}:
      self.drawpad = drawpad(self, self.logger)

  def callback(self):   
    with self.onf_dict_lock:
      for item in self.onf_dict.values():
        item(self)

  def push_to_onf(self, onf):
    count = 0
    with self.onf_dict_lock:
      while count in self.onf_dict:
        count += 1
      self.onf_dict[count] = onf
    return(count)

  def pop_from_onf(self, count):
    with self.onf_dict_lock:
      del self.onf_dict[count]

  def stop(self):
    self.inqueue.stop()
#    for thread in enumerate(): 
#      print(thread)

