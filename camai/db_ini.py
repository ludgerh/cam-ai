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

def db_ini():
  if not model_type.objects.filter(name='efficientnetv2-b0'):
    newtype = model_type(name='efficientnetv2-b0', x_in_default=224, y_in_default=224)
    newtype.save()
  if not model_type.objects.filter(name='efficientnetv2-b1'):
    newtype = model_type(name='efficientnetv2-b1', x_in_default=240, y_in_default=240)
    newtype.save()
  if not model_type.objects.filter(name='efficientnetv2-b2'):
    newtype = model_type(name='efficientnetv2-b2', x_in_default=260, y_in_default=260)
    newtype.save()
  if not model_type.objects.filter(name='efficientnetv2-b3'):
    newtype = model_type(name='efficientnetv2-b3', x_in_default=300, y_in_default=300)
    newtype.save()
  #if not model_type.objects.filter(name='efficientnetv2-s'):
  #  newtype = model_type(name='efficientnetv2-s', x_in_default=384, y_in_default=384)
  #  newtype.save()
  #if not model_type.objects.filter(name='efficientnetv2-m'):
  #  newtype = model_type(name='efficientnetv2-m', x_in_default=480, y_in_default=480)
  #  newtype.save()
  #if not model_type.objects.filter(name='efficientnetv2-l'):
  #  newtype = model_type(name='efficientnetv2-l', x_in_default=480, y_in_default=480)
  #  newtype.save()
    
if not  camurl.objects.filter(type='Imou Cruiser SE+'):
  newcam = camurl(type='Imou Cruiser SE+', 
    url='rtsp://{user}:{pass}@{address}:{port}/cam/realmonitor?channel=1&subtype=0')
  newcam.save()
if not  camurl.objects.filter(type='levelone FCS-4051'):
  newcam = camurl(type='levelone FCS-4051', 
    url='rtsp://{user}:{pass}@{address}:{port}/Streaming/Channels/101?transportmode=mcast&profile=Profile_1')
  newcam.save()
if not  camurl.objects.filter(type='levelone FCS-5201'):
  newcam = camurl(type='levelone FCS-5201', 
    url='rtsp://{user}:{pass}@{address}:{port}/Streaming/Channels/101?transportmode=mcast&profile=Profile_1')
  newcam.save()
if not  camurl.objects.filter(type='Novus NVIP-4VE-6501'):
  newcam = camurl(type='Novus NVIP-4VE-6501', 
    url='rtsp://{user}:{pass}@{address}:{port}/profile1',
    reduce_latence = False,
  )
  newcam.save()
if not  camurl.objects.filter(type='Novus NVR-34XX'):
  newcam = camurl(type='Novus NVR-34XX', 
    url='rtsp://{user}:{pass}@{address}:{port}/H264?ch=1&subtype=0')
  newcam.save()
if not  camurl.objects.filter(type='Reolink RLC-410W'):
  newcam = camurl(type='Reolink RLC-410W', 
    url='rtmp://{address}:{port}/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={pass}')
  newcam.save()
if not  camurl.objects.filter(type='Reolink E1 Zoom'):
  newcam = camurl(type='Reolink E1 Zoom', 
    url='rtmp://{address}:{port}/bcs/channel0_main.bcs?channel=0&stream=1&user={user}&password={pass}')
  newcam.save()
if not  camurl.objects.filter(type='TP-Link Tapo C200'):
  newcam = camurl(type='TP-Link Tapo C200', 
    url='rtsp://{user}:{pass}@{address}:{port}/stream1')
  newcam.save()

if alarm_device_type.objects.filter(name='console'):
  new_type = alarm_device_type.objects.get(name='console')
else:  
  new_type = alarm_device_type(
    name='console', 
    mendef='[["s", "Output", "We had an alarm..."]]', 
  )
  new_type.save()
  
if not alarm_device_type.objects.filter(name='shelly123'):
  new_type = alarm_device_type(
    name='shelly123', 
    mendef='[["s", "IP", "1.2.3.4"]]', 
  )
  new_type.save()
  
if not alarm_device_type.objects.filter(name='hue'):
  new_type = alarm_device_type(
    name='hue', 
    mendef='[["s", "IP", "1.2.3.4"], ["s", "User", "user"]]', 
  )
  new_type.save()
  
if not alarm_device_type.objects.filter(name='taposwitch123'):
  new_type = alarm_device_type(
    name='taposwitch123', 
    mendef='[["s", "IP", "1.2.3.4"]]', 
  )
  new_type.save()
  
if not alarm_device_type.objects.filter(name='proxy-gpio'):
  new_type = alarm_device_type(
    name='proxy-gpio', 
    mendef='[["s", "IP", "1.2.3.4"], ["i", "channel", 1]]', 
  )
  new_type.save()
  
if not alarm_device.objects.filter(name='console'):
  new_device = alarm_device(
    name='console', 
    device_type=new_type, 
  )
  new_device.save()
  
