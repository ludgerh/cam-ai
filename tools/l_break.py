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

from time import sleep as t_sleep
from asyncio import sleep as a_sleep

def break_time(seconds):
  t_sleep(seconds)
  
async def a_break_time(seconds):
  await a_sleep(seconds)
  
TZ_STANDARD = 0

BR_VSHORT = 0
BR_SHORT = 1
BR_MEDIUM = 2
BR_LONG = 3

breaks = (
  (0.001, ),
  (0.01, ),   
  (0.1, ),   
  (1.0, ),  
) 

def break_type(length = 0, time_zone = 0):
  t_sleep(breaks[length][time_zone])
  
async def a_break_type(length = 0, time_zone = 0):
  await a_sleep(breaks[length][time_zone])
  
class a_break_auto():
  def __init__(self, tmin = 0.01, tmax = 1.0, rate = 0.01, start = None):
    self.tmin = tmin
    self.tmax = tmax
    self.rate = rate
    if start:
      self.wait_time = start
    else:
      self.wait_time = tmax
          
  def reset(self):
    self.wait_time = self.tmin
    
  async def wait(self):
    await a_sleep(self.wait_time)
    self.wait_time = min(self.tmax, self.wait_time + self.rate)
      

