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

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.http import HttpResponse
try:  
  from camai.passwords import emulatestatic
except  ImportError: # can be removed when everybody is up to date
  emulatestatic = False
from streams.models import stream
from access.c_access import access
from tf_workers.models import school
from tools.l_tools import djconf
from camai.passwords import os_type

class health(LoginRequiredMixin, TemplateView):
  template_name = 'cleanup/cleanup.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    datapath = djconf.getconfig('datapath', 'data/')
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        self.request.user, 'R'
      ),
      'streamlist_write' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        self.request.user, 'W'
      ),
      'detectorlist' : access.filter_items(
        stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', 
        self.request.user, 'R'
      ),
      'eventerlist' : access.filter_items(
        stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', 
        self.request.user, 'R'
      ),
      'schoollist' : access.filter_items(
        school.objects.filter(active=True), 'S', 
        self.request.user, 'R'
      ),
      'schoollist_write' : access.filter_items(
        school.objects.filter(active=True), 'S', 
        self.request.user, 'W'
      ),
      'os_type' : os_type[:3],
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
      
