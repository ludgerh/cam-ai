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

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
try:  
  from camai.passwords import emulatestatic
except  ImportError: # can be removed when everybody is up to date
  emulatestatic = False
from access.c_access import access
from streams.models import stream
from startup.startup import streams
from tools.l_tools import djconf
from tools.tokens import checktoken
from tf_workers.models import school
from .forms import CamForm , DetectorForm, EventerForm
from camai.passwords import os_type

@login_required
def onecam(request, camnr, tokennr=0, token=None):
  if request.user.id is None:
    if (tokennr and token):
      go_on = checktoken((tokennr, token), 'CAR', camnr)
      may_write = False
    else:
      go_on = False
  else:
    go_on = access.check('C', camnr, request.user, 'R')
    may_write = access.check('C', camnr, request.user, 'W')
  if not go_on:
    return(HttpResponse('No Access!'))
  dbline = stream.objects.get(id=camnr)
  mycam = streams[camnr].mycam
  myurl = '/oneitem/cam/'
  if request.method == 'POST':
    form = CamForm(request.POST)
    if form.is_valid():
      dbline.name = form.cleaned_data['name']
      dbline.cam_pause = form.cleaned_data['cam_pause']
      dbline.cam_url = form.cleaned_data['cam_url']
      dbline.cam_fpslimit = form.cleaned_data['cam_fpslimit']
      dbline.cam_ffmpeg_fps = form.cleaned_data['cam_ffmpeg_fps']
      dbline.cam_red_lat = form.cleaned_data['cam_red_lat']
      dbline.cam_checkdoubles = form.cleaned_data['cam_checkdoubles']
      dbline.save(update_fields=[
        'name',
        'cam_pause',
        'cam_fpslimit', 
        'cam_ffmpeg_fps', 
        'cam_url',
        'cam_red_lat',
        'cam_checkdoubles',
      ])
      mycam.inqueue.put(('reset_cam',))
      return HttpResponseRedirect(myurl+str(camnr)+'/')
  else:
    form = CamForm(initial={
      'name' : dbline.name,
      'cam_pause' : dbline.cam_pause,
      'cam_fpslimit' : dbline.cam_fpslimit,
      'cam_ffmpeg_fps' : dbline.cam_ffmpeg_fps,
      'cam_url' : dbline.cam_url,
      'cam_red_lat' : dbline.cam_red_lat,
      'cam_checkdoubles' : dbline.cam_checkdoubles,
    })
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        request.user, 'R'
      ),
      'detectorlist' : access.filter_items(
        stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', 
        request.user, 'R'
      ),
      'eventerlist' : access.filter_items(
        stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', 
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
      'myurl' : myurl,
      'form' : form,
      'os_type' : os_type[:3],
    }
  return(render(request, 'oneitem/onecam.html', context))

@login_required
def onedetector(request, detectornr, tokennr=0, token=None):
  if request.user.id is None:
    if (tokennr and token):
      go_on = checktoken((tokennr, token), 'DER', detectornr)
      may_write = False
    else:
      go_on = False
  else:
    go_on = access.check('D', detectornr, request.user, 'R')
    may_write = access.check('D', detectornr, request.user, 'W')
  if not go_on:
    return(HttpResponse('No Access!'))
  dbline = stream.objects.get(id=detectornr)
  mydetector = streams[detectornr].mydetector
  myurl = '/oneitem/detector/'
  if request.method == 'POST':
    form = DetectorForm(request.POST)
    if form.is_valid():
      streams[detectornr].dbline.det_fpslimit = form.cleaned_data['det_fpslimit']
      streams[detectornr].dbline.det_threshold = form.cleaned_data['det_threshold']
      streams[detectornr].dbline.det_backgr_delay = form.cleaned_data['det_backgr_delay']
      streams[detectornr].dbline.det_dilation = form.cleaned_data['det_dilation']
      streams[detectornr].dbline.det_erosion = form.cleaned_data['det_erosion']
      streams[detectornr].dbline.det_max_size = form.cleaned_data['det_max_size']
      streams[detectornr].dbline.det_max_rect = form.cleaned_data['det_max_rect']
      streams[detectornr].dbline.det_scaledown = form.cleaned_data['det_scaledown']
      streams[detectornr].dbline.save(update_fields=[
        'det_fpslimit', 
        'det_threshold',
        'det_backgr_delay',
        'det_dilation',
        'det_erosion',
        'det_max_size',
        'det_max_rect',
        'det_scaledown',
      ])
      mydetector.reset()
      return HttpResponseRedirect(myurl+str(detectornr)+'/')
  else:
    form = DetectorForm(initial={
      'det_fpslimit' : dbline.det_fpslimit,
      'det_threshold' : dbline.det_threshold,
      'det_backgr_delay' : dbline.det_backgr_delay,
      'det_dilation' : dbline.det_dilation,
      'det_erosion' : dbline.det_erosion,
      'det_max_size' : dbline.det_max_size,
      'det_max_rect' : dbline.det_max_rect,
      'det_scaledown' : dbline.det_scaledown,
    })
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        request.user, 'R'
      ),
      'detectorlist' : access.filter_items(
        stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', 
        request.user, 'R'
      ),
      'eventerlist' : access.filter_items(
        stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', 
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
      'myurl' : myurl,
      'form' : form,
      'os_type' : os_type[:3],
    }
  return(render(request, 'oneitem/onedetector.html', context))

@login_required
def oneeventer(request, eventernr, tokennr=0, token=None):
  if request.user.id is None:
    if (tokennr and token):
      go_on = checktoken((tokennr, token), 'ETR', eventernr)
      may_write = False
    else:
      go_on = False
  else:
    go_on = access.check('E', eventernr, request.user, 'R')
    may_write = access.check('E', eventernr, request.user, 'W')
  if not go_on:
    return(HttpResponse('No Access!'))
  dbline = stream.objects.get(id=eventernr)
  myeventer = streams[eventernr].mydetector.myeventer
  myurl = '/oneitem/eventer/'
  if request.method == 'POST':
    form = EventerForm(request.POST)
    if form.is_valid():
      streams[eventernr].dbline.eve_fpslimit = form.cleaned_data['eve_fpslimit']
      streams[eventernr].dbline.eve_margin = form.cleaned_data['eve_margin']
      streams[eventernr].dbline.eve_event_time_gap = form.cleaned_data['eve_event_time_gap']
      streams[eventernr].dbline.eve_shrink_factor = form.cleaned_data['eve_shrink_factor']
      streams[eventernr].dbline.eve_sync_factor = form.cleaned_data['eve_sync_factor']
      streams[eventernr].dbline.eve_school = form.cleaned_data['eve_school']
      streams[eventernr].dbline.eve_alarm_email = form.cleaned_data['eve_alarm_email']
      streams[eventernr].dbline.save(update_fields=[
        'eve_fpslimit', 
        'eve_margin',
        'eve_event_time_gap',
        'eve_shrink_factor',
        'eve_sync_factor',
        'eve_school',
        'eve_alarm_email',
      ])
      myeventer.reset()
      return HttpResponseRedirect(myurl+str(eventernr)+'/')
  else:
    form = EventerForm(initial={
      'eve_fpslimit' : dbline.eve_fpslimit,
      'eve_margin' : dbline.eve_margin,
      'eve_event_time_gap' : dbline.eve_event_time_gap,
      'eve_shrink_factor' : dbline.eve_shrink_factor,
      'eve_sync_factor' : dbline.eve_sync_factor,
      'eve_school' : dbline.eve_school,
      'eve_alarm_email' : dbline.eve_alarm_email,
    })
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        request.user, 'R'
      ),
      'detectorlist' : access.filter_items(
        stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', 
        request.user, 'R'
      ),
      'eventerlist' : access.filter_items(
        stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', 
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
      'myurl' : myurl,
      'form' : form,
      'os_type' : os_type[:3],
    }
  return(render(request, 'oneitem/oneeventer.html', context))
