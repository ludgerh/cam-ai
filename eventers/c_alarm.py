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

import os
from .models import alarm as dbalarm
from .alarm_base import alarm_base

#check which plugins are present:
plugin_shelly_ok = os.path.exists('plugins/cam_ai_shelly')
if plugin_shelly_ok:
  from plugins.cam_ai_shelly.shelly import shelly123_alarm
plugin_hue_ok = os.path.exists('plugins/cam_ai_hue')
if plugin_hue_ok:
  from plugins.cam_ai_hue.hue import hue_alarm
  
mylogger = None 
alarm_list = None
  
def alarm_init(logger, idx):
  global mylogger
  global alarm_list
  mylogger = logger  
  alarm_list = []
  for item in dbalarm.objects.filter(active=True, mystream__id=idx):
    if item.mydevice.device_type.name == 'console':
      alarm_list.append(console_alarm(item, mylogger))
    elif item.mydevice.device_type.name == 'shelly123':
      if plugin_shelly_ok:  
        alarm_list.append(shelly123_alarm(item, mylogger))
      else:
        mylogger.warning('***** For alarm device shelly123 we need the shelly-plugin, '
          + 'ignoring this alarm.')   
    elif item.mydevice.device_type.name == 'hue':
      if plugin_hue_ok:  
        alarm_list.append(hue_alarm(item, mylogger))
      else:
        mylogger.warning('***** For alarm device phillips hue we need the hue-plugin, '
          + 'ignoring this alarm.') 

class console_alarm(alarm_base):

  def __init__(self, dbline, logger):
    super().__init__(dbline, logger)
    self.notice_line = self.params[0]
    
  def action(self, pred): 
    super().action(pred=pred)
    self.logger.info(self.notice_line + ' ' + self.stream.name + '(' + str(self.stream.id) 
      + ') : ' + self.classes_list[self.maxpos+1].name +  ' Sebi testet die Konsole')

def alarm(stream_id, pred):
  for item in alarm_list:
    item.action(pred=pred)
