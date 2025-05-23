"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
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
import asyncio
from time import sleep
from .models import alarm as dbalarm
from .alarm_base import alarm_base, init_failed_exception

#check which plugins are present:
plugin_shelly_ok = os.path.exists('plugins/cam_ai_shelly')
if plugin_shelly_ok:
  from plugins.cam_ai_shelly.shelly import shelly123_alarm
plugin_hue_ok = os.path.exists('plugins/cam_ai_hue')
if plugin_hue_ok:
  from plugins.cam_ai_hue.hue import hue_alarm
plugin_taposwitch_ok = os.path.exists('plugins/cam_ai_taposwitch')
if plugin_taposwitch_ok:
  from plugins.cam_ai_taposwitch.taposwitch import taposwitch123_alarm
plugin_proxy_ok = os.path.exists('plugins/cam_ai_proxy')
if plugin_proxy_ok:
  from plugins.cam_ai_proxy.proxy import proxy_gpio_alarm
  
mylogger = None 
alarm_list = []
  
def alarm_init(logger, idx):
  global mylogger
  global alarm_list
  mylogger = logger  
  for item in dbalarm.objects.filter(active=True, mystream__id=idx):
    device_type_name = item.mydevice.device_type.name
    if device_type_name == 'console':
      alarm_list.append(console_alarm(item, mylogger))
    elif device_type_name == 'shelly123':
      if plugin_shelly_ok:  
        alarm_list.append(shelly123_alarm(item, mylogger))
      else:
        mylogger.warning('***** For alarm device shelly123 we need the shelly-plugin, '
          + 'ignoring this alarm.')   
    elif device_type_name == 'hue':
      if plugin_hue_ok:  
        alarm_list.append(hue_alarm(item, mylogger))
      else:
        mylogger.warning('***** For alarm device phillips hue we need the hue-plugin, '
          + 'ignoring this alarm.') 
    elif device_type_name == 'taposwitch123':
      if plugin_taposwitch_ok:  
        alarm_list.append(taposwitch123_alarm(item, mylogger))
      else:
        mylogger.warning('***** For alarm device taposwitch123 we need the hue-plugin, '
          + 'ignoring this alarm.') 
    elif device_type_name == 'proxy-gpio':
      if plugin_proxy_ok:  
        while True:
          try:
            alarm_list.append(proxy_gpio_alarm(item, mylogger))
            break
          except init_failed_exception as e:
            mylogger.warning('!!!!! Proxy init failed: ' + str(e)) 
      else:
        mylogger.warning('***** For alarm device proxy-gpio we need the proxy-plugin, '
          + 'ignoring this alarm.') 

class console_alarm(alarm_base):

  def __init__(self, dbline, logger):
    super().__init__(dbline, logger)
    self.notice_line = self.params[0]
    
  async def action(self, pred): 
    await super().action(pred=pred)
    self.logger.info(self.notice_line + ' ' + self.stream.name + '(' + str(self.stream.id) 
      + ') : ' + self.classes_list[self.maxpos+1].name)

async def alarm(stream_id, pred):
  tasks = [item.action(pred=pred) for item in alarm_list]
  await asyncio.gather(*tasks)
