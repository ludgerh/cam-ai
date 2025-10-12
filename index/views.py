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

from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from camai.c_settings import safe_import
from access.c_access import access
from streams.models import stream
from tf_workers.models import school
from tools.l_tools import djconf

emulatestatic = safe_import('emulatestatic') 

@login_required
def index(request, mode='C'):
  template = loader.get_template('index/index.html')
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'emulatestatic' : emulatestatic,
    'debug' : settings.DEBUG,
    'mode' : mode,
    'tf_debug' : request.user.is_superuser and djconf.getconfigbool('do_tf_debug', True),
    'camlist' : access.filter_items(
      stream.objects.filter(active=True).filter(cam_mode_flag__gt=0, demo=0), 'C', 
      request.user, 'R'
    ),
    'detectorlist' : access.filter_items(
      stream.objects.filter(active=True).filter(det_mode_flag__gt=0, demo=0), 'D', 
      request.user, 'R'
    ),
    'eventerlist' : access.filter_items(
      stream.objects.filter(active=True).filter(eve_mode_flag__gt=0, demo=0), 'E', 
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
    'emulatestatic' : emulatestatic,
    'debug' : settings.DEBUG,
    'mode' : mode,
    'camlist' : access.filter_items(
      stream.objects.filter(active=True).filter(cam_mode_flag__gt=0, demo=0), 'C', 
      request.user, 'R'
    ),
    'detectorlist' : access.filter_items(
      stream.objects.filter(active=True).filter(det_mode_flag__gt=0, demo=0), 'D', 
      request.user, 'R'
    ),
    'eventerlist' : access.filter_items(
      stream.objects.filter(active=True).filter(eve_mode_flag__gt=0, demo=0), 'E', 
      request.user, 'R'
    ),
    'user' : request.user,
  }
  return(HttpResponse(template.render(context)))

def landing(request):
  template = loader.get_template('index/landing.html')
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'emulatestatic' : emulatestatic,
    'debug' : settings.DEBUG,
    'tf_debug' : request.user.is_superuser and djconf.getconfigbool('do_tf_debug', True),
    'camlist' : access.filter_items(
      stream.objects.filter(active=True).filter(cam_mode_flag__gt=0).order_by('-id'), 'C', 
      request.user, 'R'
    ),
    'detectorlist' : access.filter_items(
      stream.objects.filter(active=True).filter(det_mode_flag__gt=0).order_by('-id'), 'D', 
      request.user, 'R'
    ),
    'eventerlist' : access.filter_items(
      stream.objects.filter(active=True).filter(eve_mode_flag__gt=0).order_by('-id'), 'E', 
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
