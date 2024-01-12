# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from camai.passwords import emulatestatic
from access.c_access import access
from streams.models import stream
from streams.c_streams import streams
from tools.l_tools import djconf
from tools.tokens import checktoken
from tf_workers.models import school, worker
from .forms import CamForm , DetectorForm, EventerForm


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
      dbline.cam_feed_type = form.cleaned_data['cam_feed_type']
      dbline.save(update_fields=[
        'name',
        'cam_pause',
        'cam_fpslimit', 
        'cam_feed_type',
        'cam_url',
      ])
      mycam.inqueue.put(('reset_cam',))
      return HttpResponseRedirect(myurl+str(camnr)+'/')
  else:
    form = CamForm(initial={
      'name' : dbline.name,
      'cam_pause' : dbline.cam_pause,
      'cam_fpslimit' : dbline.cam_fpslimit,
      'cam_feed_type' : dbline.cam_feed_type,
      'cam_url' : dbline.cam_url,
    })
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', request.user, 'R')
    templist = access.filter_items(school.objects.filter(active=True), 'S', request.user, 'R')
    schoollist = []
    for item in templist:
      if ((item.id > 1) or (request.user.is_staff)) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'myurl' : myurl,
      'form' : form,
    }
  return(render(request, 'oneitem/onecam.html', context))

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
      streams[detectornr].dbline.save(update_fields=[
        'det_fpslimit', 
        'det_threshold',
        'det_backgr_delay',
        'det_dilation',
        'det_erosion',
        'det_max_size',
        'det_max_rect',
      ])
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
    })
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', request.user, 'R')
    templist = access.filter_items(school.objects.filter(active=True), 'S', request.user, 'R')
    schoollist = []
    for item in templist:
      if ((item.id > 1) or (request.user.is_staff)) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'myurl' : myurl,
      'form' : form,
    }
  return(render(request, 'oneitem/onedetector.html', context))

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
      streams[eventernr].dbline.eve_school = form.cleaned_data['eve_school']
      streams[eventernr].dbline.eve_alarm_email = form.cleaned_data['eve_alarm_email']
      streams[eventernr].dbline.save(update_fields=[
        'eve_fpslimit', 
        'eve_margin',
        'eve_event_time_gap',
        'eve_school',
        'eve_alarm_email',
      ])
      return HttpResponseRedirect(myurl+str(eventernr)+'/')
  else:
    form = EventerForm(initial={
      'eve_fpslimit' : dbline.eve_fpslimit,
      'eve_margin' : dbline.eve_margin,
      'eve_event_time_gap' : dbline.eve_event_time_gap,
      'eve_school' : dbline.eve_school,
      'eve_alarm_email' : dbline.eve_alarm_email,
    })
    form.fields["eve_school"].queryset = school.objects.filter(active=True)
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', request.user, 'R')
    templist = access.filter_items(school.objects.filter(active=True), 'S', request.user, 'R')
    schoollist = []
    for item in templist:
      if ((item.id > 1) or (request.user.is_staff)) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'myurl' : myurl,
      'form' : form,
    }
  return(render(request, 'oneitem/oneeventer.html', context))
