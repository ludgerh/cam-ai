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
from asgiref.sync import sync_to_async
from time import sleep
from channels.db import database_sync_to_async
from tools.l_break import a_break_type, BR_LONG
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
  from plugins.cam_ai_proxy.proxy import proxy_gpio_alarm, proxy_sound_alarm
plugin_tasmota_ok = os.path.exists('plugins/cam_ai_tasmota')
if plugin_tasmota_ok:
  from plugins.cam_ai_tasmota.tasmota import tasmota_alarm
  
mylogger = None 
alarm_dict = {}
  
def alarm_init(logger):
  global mylogger
  mylogger = logger  

class console_alarm(alarm_base):

  def __init__(self, dbline, logger):
    super().__init__(dbline, logger)
    self.notice_line = self.params[0]
    
  async def action(self, pred): 
    await super().action(pred=pred)
    self.logger.info(self.notice_line + ' ' + self.stream.name + '(' + str(self.stream.id) 
      + ') : ' + self.classes_list[self.maxpos+1].name)
      
async def make_alarm(alarm_line):
  device_type_name = alarm_line.mydevice.device_type.name
  if device_type_name == 'console':
    return(await database_sync_to_async(console_alarm)(alarm_line, mylogger))
  elif device_type_name == 'shelly123':
    if plugin_shelly_ok:  
      return(await database_sync_to_async(shelly123_alarm)(alarm_line, mylogger))
    else:
      mylogger.warning('***** For alarm device shelly123 we need the shelly-plugin, '
        + 'ignoring this alarm.')   
  elif device_type_name == 'hue':
    if plugin_hue_ok:  
      return(await database_sync_to_async(hue_alarm)(alarm_line, mylogger))
    else:
      mylogger.warning('***** For alarm device phillips hue we need the hue-plugin, '
        + 'ignoring this alarm.') 
  elif device_type_name == 'taposwitch123':
    if plugin_taposwitch_ok:  
      return(await database_sync_to_async(taposwitch123_alarm)(alarm_line, mylogger))
    else:
      mylogger.warning('***** For alarm device taposwitch123 we need the hue-plugin, '
        + 'ignoring this alarm.') 
  elif device_type_name == 'proxy-gpio':
    if plugin_proxy_ok:  
      while True:
        try:
          return(await database_sync_to_async(proxy_gpio_alarm)(alarm_line, mylogger))
          break
        except init_failed_exception as e:
          mylogger.warning('!!!!! Proxy init failed: ' + str(e)) 
          await a_break_type(BR_LONG)
    else:
      mylogger.warning('***** For alarm device proxy-gpio we need the proxy-plugin, '
        + 'ignoring this alarm.') 
  elif device_type_name == 'proxy-sound':
    if plugin_proxy_ok:  
      while True:
        try:
          return(await database_sync_to_async(proxy_sound_alarm)(alarm_line, mylogger))
        except init_failed_exception as e:
          mylogger.warning('!!!!! Proxy init failed: ' + str(e)) 
          await a_break_type(BR_LONG)
    else:
      mylogger.warning('***** For alarm device proxy-sound we need the proxy-plugin, '
        + 'ignoring this alarm.')  
  elif device_type_name == 'tasmota':
    if plugin_tasmota_ok:  
      while True:
        try:
          return(await database_sync_to_async(tasmota_alarm)(alarm_line, mylogger))
        except init_failed_exception as e:
          mylogger.warning('!!!!! Tasmota init failed: ' + str(e)) 
          await a_break_type(BR_LONG)
    else:
      mylogger.warning('***** For alarm device tasmota we need the tasmota-plugin, '
        + 'ignoring this alarm.')   

async def alarm(stream_id, pred):
  items = await sync_to_async(
    lambda: list(
      dbalarm.objects
      .filter(active=True, mystream__id=stream_id)
      .select_related("mydevice__device_type")
    )
  )()
  if items:
    new_alarm_dict = {}
    for item in items:
      new_alarm_dict[item.id] = item
    for i, item in new_alarm_dict.items():
      if i not in alarm_dict:
        alarm_dict[i] = await make_alarm(item)
      else:
        if (item.mendef != alarm_dict[i].mendef
            or item.mydevice_id != alarm_dict[i].device_id):
          alarm_dict[i] = await make_alarm(item)
    for i in list(alarm_dict):
      if i not in new_alarm_dict:
        del alarm_dict[i]  
    tasks = [item.action(pred=pred) for item in alarm_dict.values()]
    await asyncio.gather(*tasks)
