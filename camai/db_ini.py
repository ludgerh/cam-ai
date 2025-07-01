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

from trainers.models import model_type
from tools.models import camurl
from eventers.models import alarm_device_type, alarm_device

async def add_if_none(table, index, params):
  result = 0
  try:
    await table.objects.aget(**{index : params[index], })
  except table.DoesNotExist:
    new_line = table(**params)
    await new_line.asave()
    result = new_line
  except table.MultipleObjectsReturned:
    pass
  return(result)  
    

async def db_ini():
  await add_if_none(model_type, 'name', {
    'name' : 'efficientnetv2-b0',
    'x_in_default' : 224, 
    'y_in_default' : 224,
  })
  await add_if_none(model_type, 'name', {
    'name' : 'efficientnetv2-b1',
    'x_in_default' : 240, 
    'y_in_default' : 240,
  })
  await add_if_none(model_type, 'name', {
    'name' : 'efficientnetv2-b2',
    'x_in_default' : 260, 
    'y_in_default' : 260,
  })
  await add_if_none(model_type, 'name', {
    'name' : 'efficientnetv2-b3',
    'x_in_default' : 300, 
    'y_in_default' : 300,
  })
  
  await add_if_none(camurl, 'type', {
    'type' : 'Imou Cruiser SE+',
    'url' : 'rtsp://{user}:{pass}@{address}:{port}/cam/realmonitor?channel=1&subtype=0', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'levelone FCS-4051',
    'url' : 'rtsp://{user}:{pass}@{address}:{port}/Streaming/Channels/101?transportmode=mcast&profile=Profile_1', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'levelone FCS-5201',
    'url' : 'rtsp://{user}:{pass}@{address}:{port}/Streaming/Channels/101?transportmode=mcast&profile=Profile_1', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'Instar IN-5907 HD',
    'url' : 'rtsp://{user}:{pass}@{address}:{port}/11', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'Novus NVIP-4VE-6501',
    'url' : 'rtsp://{user}:{pass}@{address}:{port}/profile1', 
    'reduce_latence' : False, 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'Novus NVR-34XX',
    'url' : 'rtsp://{user}:{pass}@{address}:{port}/H264?ch=1&subtype=0', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'Reolink RLC-410W',
    'url' : 'rtmp://{address}:{port}/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={pass}', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'Reolink E1 Zoom',
    'url' : 'rtmp://{address}:{port}/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={pass}', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'TP-Link Tapo C200',
    'url' : 'rtsp://{user}:{pass}@{address}:{port}/stream1', 
  })
  await add_if_none(camurl, 'type', {
    'type' : 'Wyze CAM V2 with Dafang Hacks',
    'url' : 'rtsp://{address}:{port}/unicast', 
  })
  
  new_type = await add_if_none(alarm_device_type, 'name', {
    'name' : 'console',
    'mendef' : '[["s", "Output", "We had an alarm..."]]', 
  })
  if new_type:
    await add_if_none(alarm_device, 'name', {
      'name' : 'console',
      'device_type' : new_type, 
    })
  await add_if_none(alarm_device_type, 'name', {
    'name' : 'shelly123',
    'mendef' : '[["s", "IP", "1.2.3.4"]]', 
  })
  await add_if_none(alarm_device_type, 'name', {
    'name' : 'hue',
    'mendef' : '[["s", "IP", "1.2.3.4"], ["s", "User", "user"]]', 
  })
  await add_if_none(alarm_device_type, 'name', {
    'name' : 'taposwitch123',
    'mendef' : '[["s", "IP", "1.2.3.4"]]', 
  })
  await add_if_none(alarm_device_type, 'name', {
    'name' : 'proxy-gpio',
    'mendef' : '[["s", "IP", "1.2.3.4"], ["i", "channel", 1]]', 
  })
  
