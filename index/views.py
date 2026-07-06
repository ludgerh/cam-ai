"""
Copyright (C) 2024-2026 by the CAM-AI team, info@cam-ai.de
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

from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from access.c_access import access
from streams.models import stream
from tf_workers.models import school
from tools.l_tools import djconf

@login_required
def index(request, mode='C'):
  template = loader.get_template('index/index.html')
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'debug' : settings.DEBUG,
    'mode' : mode,
    'tf_debug' : request.user.is_superuser and djconf.getconfigbool('do_tf_debug', True),
    'camlist' : access.filter_items(
      stream.objects.filter(active=True).filter(cam_mode_flag__gt=0, demo=False), 'C', 
      request.user, 'R'
    ),
    'detectorlist' : access.filter_items(
      stream.objects.filter(active=True).filter(det_mode_flag__gt=0, demo=False), 'D', 
      request.user, 'R'
    ),
    'eventerlist' : access.filter_items(
      stream.objects.filter(active=True).filter(eve_mode_flag__gt=0, demo=False), 'E', 
      request.user, 'R'
    ),
    'schoollist' : access.filter_items(
      school.objects.filter(active=True), 'S', 
      request.user, 'R'
    ),
    'schoollist_write' : access.filter_items(
      school.objects.filter(active=True), 'S', 
      request.user, 'W'
    ),
    'user' : request.user,
  }
  return(HttpResponse(template.render(context)))
  
def indexgrid(request, mode='C', start=0, end=0):
  template = loader.get_template('index/indexgrid.html')
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'debug' : settings.DEBUG,
    'mode' : mode,
    'camlist' : access.filter_items(
      stream.objects.filter(active=True).filter(cam_mode_flag__gt=0, demo=False), 'C', 
      request.user, 'R'
    ),
    'detectorlist' : access.filter_items(
      stream.objects.filter(active=True).filter(det_mode_flag__gt=0, demo=False), 'D', 
      request.user, 'R'
    ),
    'eventerlist' : access.filter_items(
      stream.objects.filter(active=True).filter(eve_mode_flag__gt=0, demo=False), 'E', 
      request.user, 'R'
    ),
    'user' : request.user,
  }
  return(HttpResponse(template.render(context)))

def landing(request, start=0):
  max_num_cams = djconf.getconfigint('max_num_cams', 3)
  template = loader.get_template('index/landing.html')
  full_cam_list = access.filter_items(
      stream.objects.filter(active=True).filter(cam_mode_flag__gt=0).order_by('id'), 'C', 
      request.user, 'R'
  )
  full_det_list = access.filter_items(
      stream.objects.filter(active=True).filter(det_mode_flag__gt=0).order_by('id'), 'D', 
      request.user, 'R'
  )
  full_eve_list = access.filter_items(
      stream.objects.filter(active=True).filter(eve_mode_flag__gt=0).order_by('id'), 'E', 
      request.user, 'R'
  )
  pos_string = ''
  for i in range(len(full_cam_list)):
    if i == start:
      pos_string += '['
    pos_string += '•'
    if i == start + max_num_cams - 1:
      pos_string += ']'
     
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'debug' : settings.DEBUG,
    'tf_debug' : request.user.is_superuser and djconf.getconfigbool('do_tf_debug', True),
    'camlist' : full_cam_list,
    'detectorlist' : full_det_list,
    'eventerlist' : full_eve_list,
    'partial_cam_list' : full_cam_list[start:start + max_num_cams],
    'cam_count' : len(full_cam_list),
    'cam_start' : start,
    'cam_width' : max_num_cams,
    'pos_string' : pos_string,
    'cam_width' : max_num_cams,
    'pos_string' : pos_string,
    'pos_prev' : max(start - 1, 0),
    'pos_next' : min(start + 1, len(full_cam_list) - 1),
    'schoollist' : access.filter_items(
      school.objects.filter(active=True), 'S', 
      request.user, 'R'
    ),
    'schoollist_write' : access.filter_items(
      school.objects.filter(active=True), 'S', 
      request.user, 'W'
    ),
    'user' : request.user,
  }
  return(HttpResponse(template.render(context)))
