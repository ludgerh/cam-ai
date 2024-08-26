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

import base64
from logging import getLogger
from urllib.parse import parse_qs
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User
from tools.c_logger import log_ini
from access.c_access import access
from streams.models import stream
from streams.startup import streams

logname = 'dyndns'
logger = getLogger(logname)
log_ini(logger, logname)

def update(request, new_ip, task_url):
  user = None
  if 'HTTP_AUTHORIZATION' in request.META:
    auth = request.META['HTTP_AUTHORIZATION'].split()
    if len(auth) == 2:
      if auth[0].lower() == "basic":
        name, passwd = base64.b64decode(auth[1]).decode("utf-8", "ignore").split(':')
        try:
          user = User.objects.get(username=name)
        except User.DoesNotExist:
          logger.info('DynDNS Update failed: User ' + name + ' does not exist.')
          user = None 
        if user:  
          if not user.check_password(passwd):
            logger.info('DynDNS Update failed: User ' + name + ' used wrong password.')
            user = None
  if user:
    tasklist = task_url.split('.')[0].split('-')
    if tasklist[0].upper() == 'ALL':
      streamlines = access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', user, 'W'
      )
      tasklist = [item.id for item in streamlines]
      auth_checked = True
    else:  
      auth_checked = False
    for item in tasklist:
      stream_nr = int(item)
      if auth_checked:
        auth_this_one = True
      else:  
        auth_this_one = access.check('C', stream_nr, user, 'W')
      if auth_this_one:  
        streamline = stream.objects.get(id=stream_nr)
        if streamline.cam_control_ip == new_ip:
          logger.info('DynDNS Update: User ' + name + ' skipped stream #' + str(stream_nr) + ', is already ' + new_ip)
        else:
          streamline.cam_control_ip = new_ip
          streamline.save(update_fields=['cam_control_ip'])
          streams[stream_nr].mycam.inqueue.put(('reset_cam', ))
          logger.info('DynDNS Update: User ' + name + ' changed stream #'+str(stream_nr) + ' to ' + new_ip)
    return('good')  
  else:  
    return('badauth')    

class dyndns1(View):
  def get(self, request, *args, **kwargs):
    new_ip = parse_qs(request.scope['query_string'].decode())['myip'][0]
    task_url = parse_qs(request.scope['query_string'].decode())['host_id'][0]
    returncode = update(request, new_ip, task_url)
    result = '<TITLE>CAM-AI Server</TITLE>\n'
    if returncode == 'good':
      result += 'return code : NOERROR\n'
      result += 'error code : NOERROR'
    else:  
      result += 'return code : ERROR\n'
      result += 'error code : ERROR'
    return HttpResponse(result, content_type='text/plain')

class dyndns2(View):
  def get(self, request, *args, **kwargs):
    new_ip = parse_qs(request.scope['query_string'].decode())['myip'][0]
    task_url = parse_qs(request.scope['query_string'].decode())['hostname'][0]
    returncode = update(request, new_ip, task_url)
    return HttpResponse(returncode + ' ' + new_ip, content_type='text/plain')

class checkip(View):
  def get(self, request, *args, **kwargs):
    headers_dict = dict(request.scope['headers'])
    if b'x-real-ip' in headers_dict:
      client_ip = headers_dict[b'x-real-ip'].decode()
    else:
      client_ip = 'Server is not configured for CHECKIP' 
    #logger.info(str(request.scope['headers']))
    return HttpResponse(client_ip, content_type='text/plain')

