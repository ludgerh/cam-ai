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

from urllib.parse import parse_qs
from django.shortcuts import render
from django.http import HttpResponse
from django.views import View
from streams.models import stream
from streams.startup import streams

def update(new_ip, stream_nr):
  print('...switching stream #'+str(stream_nr), 'to', new_ip)
  streamline = stream.objects.get(id=stream_nr)
  streamline.cam_control_ip = new_ip
  streamline.save(update_fields=['cam_control_ip'])
  streams[stream_nr].mycam.inqueue.put(('reset_cam', ))
  
  

class dyndns1(View):
  def get(self, request, *args, **kwargs):
    new_ip = parse_qs(request.scope['query_string'].decode())['myip'][0]
    stream_nr = int(
      parse_qs(request.scope['query_string'].decode())['host_id'][0].split('.')[0])
    update(new_ip, stream_nr)
    result = '<TITLE>CAM-AI Server</TITLE>\n'
    result += 'return code : NOERROR\n'
    result += 'error code : NOERROR'
    return HttpResponse(result, content_type='text/plain')

class dyndns2(View):
  def get(self, request, *args, **kwargs):
    new_ip = parse_qs(request.scope['query_string'].decode())['myip'][0]
    stream_nr = int(
      parse_qs(request.scope['query_string'].decode())['hostname'][0].split('.')[0])
    update(new_ip, stream_nr)
    return HttpResponse('good '+new_ip, content_type='text/plain')

