# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
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

from django.conf import settings
from django.views.generic.base import TemplateView
from django.shortcuts import render
from django.http import HttpResponse
from streams.models import stream
from users.models import userinfo
from access.c_access import access
from tf_workers.models import school, worker
from tools.l_tools import djconf
from .models import camurl

class health(TemplateView):
  template_name = 'tools/health.html'

  def get_context_data(self, **kwargs):
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    schoollist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'recordingspath' : djconf.getconfig('recordingspath', 'data/recordings/'),
      'schoolframespath' : djconf.getconfig('schoolframespath', 'data/schoolframes/')
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))

class addstream(TemplateView):
  template_name = 'tools/addstream.html'

  def get_context_data(self, **kwargs):
    streamlimit = userinfo.objects.get(user = self.request.user.id).allowed_streams
    streamcount = stream.objects.filter(creator = self.request.user.id, active = True, ).count()
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    schoollist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'camurls' : camurl.objects.all(),
      'streamlimit' : streamlimit,
      'streamcount' : streamcount,
      'mayadd' : (streamlimit > streamcount),
    })
    return context

class addonvif(TemplateView):
  template_name = 'tools/addonvif.html'

  def get_context_data(self, **kwargs):
    streamlimit = userinfo.objects.get(user = self.request.user.id).allowed_streams
    streamcount = stream.objects.filter(creator = self.request.user.id, active = True, ).count()
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    schoollist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'camurls' : camurl.objects.all(),
      'streamlimit' : streamlimit,
      'streamcount' : streamcount,
      'mayadd' : (streamlimit > streamcount),
    })
    return context

class addschool(TemplateView):
  template_name = 'tools/addschool.html'

  def get_context_data(self, **kwargs):
    schoollimit = userinfo.objects.get(user = self.request.user.id).allowed_schools
    schoolcount = school.objects.filter(creator = self.request.user.id, active = True, ).count()
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    schoollist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'schoollimit' : schoollimit,
      'schoolcount' : schoolcount,
      'mayadd' : (schoollimit > schoolcount),
    })
    return context

class linkworkers(TemplateView):
  template_name = 'tools/linkworkers.html'

  def get_context_data(self, **kwargs):
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    schoollist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'workerlist' : worker.objects.all(),
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
