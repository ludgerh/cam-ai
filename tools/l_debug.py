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

from time import time

class loop_timer():

  def __init__(self, reset_time=5.0):
    self.reset_time = reset_time
    print('*** Started loop_timer, reset_time =', self.reset_time)
    self.start_ts = time() 
    self.out_ts = time()
    self.count = 0
    self.in_ts = None
    self.in_time = 0.0
    self.out_time = 0.0
    self.total_time = 0.0
    
  def get_in(self):
    new_ts = time()
    self.out_time += new_ts - self.out_ts
    self.in_ts = new_ts   
    
  def get_out(self):
    new_ts = time()
    self.in_time += new_ts - self.in_ts
    self.out_ts = new_ts   
    
  def check(self):
    new_ts = time()
    self.count += 1
    if new_ts - self.start_ts >= self.reset_time:
      print(
        '??? count =', self.count, 
        ', freq =', round(self.count / (new_ts - self.start_ts), 3),
        ', dura =', round((new_ts - self.start_ts) / self.count, 10),
      )
      if self.in_ts:
        self.out_time += new_ts - self.out_ts
        self.total_time = new_ts - self.start_ts
        print(
          '... InSec =', round(self.in_time, 3), 
          ', OutSec =', round(self.out_time, 3),
          ', In% =', round(self.in_time / self.total_time * 100.0, 3),
          ', Out% =', round(self.out_time / self.total_time * 100.0, 3),
        )
        self.out_ts = new_ts
      self.start_ts = new_ts
      self.in_time = 0.0
      self.out_time = 0.0
      self.count = 0
