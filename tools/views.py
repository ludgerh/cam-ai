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

import json
import os
#from pprint import pprint
from requests import get as rget
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.shortcuts import render
from django.http import HttpResponse, FileResponse, HttpResponseRedirect
try:  
  from camai.passwords import emulatestatic
except  ImportError: # can be removed when everybody is up to date
  emulatestatic = False
from streams.models import stream
from users.models import userinfo
from access.c_access import access
from tf_workers.models import school, worker
from tools.l_tools import djconf
from .models import camurl
from .forms import UploadFileForm
from camai.passwords import os_type

class health(LoginRequiredMixin, TemplateView):
  template_name = 'tools/health.html'

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
      'recordingspath' : djconf.getconfig('recordingspath', datapath + 'recordings/'),
      'schoolframespath' : djconf.getconfig('schoolframespath', 
        datapath + 'schoolframes/'),
      'os_type' : os_type[:3],
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
      
class cam_inst_view(LoginRequiredMixin, TemplateView):   

  def get_context_data(self, **kwargs):
    streamlimit = userinfo.objects.get(user = self.request.user.id).allowed_streams
    streamcount = stream.objects.filter(creator = self.request.user.id, active = True, ).count()
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'is_public' : djconf.getconfigbool('is_public_server', False),
      'debug' : settings.DEBUG,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        self.request.user, 'R'
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
      'streamlimit' : streamlimit,
      'streamcount' : streamcount,
      'mayadd' : (streamlimit > streamcount),
      'os_type' : os_type[:3],
    })
    return context

class inst_cam_easy(cam_inst_view):
  template_name = 'tools/inst_cam_easy.html'

class inst_cam_expert(cam_inst_view):
  template_name = 'tools/inst_cam_expert.html'  

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'camurls' : camurl.objects.all(),
      'ipaddress' : kwargs['ip'],
      'ports' : json.loads(kwargs['ports']),
    })
    return context

class scan_cam_expert(cam_inst_view):
  template_name = 'tools/scan_cam_expert.html'

class addschool(LoginRequiredMixin, TemplateView):
  template_name = 'tools/addschool.html'

  def get_context_data(self, **kwargs):
    schoollimit = userinfo.objects.get(user = self.request.user.id).allowed_schools
    schoolcount = school.objects.filter(creator = self.request.user.id, active = True, ).count()
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        self.request.user, 'R'
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
      'schoollimit' : schoollimit,
      'schoolcount' : schoolcount,
      'mayadd' : (schoollimit > schoolcount),
      'os_type' : os_type[:3],
    })
    return context

class linkworkers(LoginRequiredMixin, TemplateView):
  template_name = 'tools/linkworkers.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        self.request.user, 'R'
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
      'workerlist' : worker.objects.all(),
      'os_type' : os_type[:3],
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))

class shutdown(TemplateView):
  template_name = 'tools/shutdown.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'emulatestatic' : emulatestatic,
      'version' : djconf.getconfig('version', 'X.Y.Z'),
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
      
class upgrade(TemplateView):
  template_name = 'tools/upgrade.html'

  def get_context_data(self, **kwargs):
    url = 'https://api.github.com/repos/ludgerh/cam-ai/releases/latest'
    response = rget(url)
    if response.status_code == 200:
      response = json.loads(response.text)
    context = super().get_context_data(**kwargs)
    context.update({
      'emulatestatic' : emulatestatic,
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'new_version' : response['tag_name'][1:],
      'zip_url' : response['zipball_url']
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
      
class backup(LoginRequiredMixin, TemplateView):
  template_name = 'tools/backup.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'emulatestatic' : emulatestatic,
      'version' : djconf.getconfig('version', 'X.Y.Z'),
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
    
def downbackup(request):
  if request.user.is_superuser:
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=backup.zip'
    response['X-Accel-Redirect'] = '/protected/backup/backup.zip'  
    return response
  else:
    return HttpResponse('No Access.')

      
#class restore(LoginRequiredMixin, TemplateView):
#  template_name = 'tools/restore.html'

#  def get_context_data(self, **kwargs):
#    context = super().get_context_data(**kwargs)
#    context.update({
#      'emulatestatic' : emulatestatic,
#      'version' : djconf.getconfig('version', 'X.Y.Z'),
#    })
#    return context

 # def get(self, request, *args, **kwargs):
 #   if self.request.user.is_superuser:
 #     return(super().get(request, *args, **kwargs))
 #   else:
 #     return(HttpResponse('No Access'))
      

def restore(request):
  if request.method == 'POST' and request.FILES['myfile']:
    myfile = request.FILES['myfile']
    fs = FileSystemStorage()
    filename = fs.save(myfile.name, myfile)
    uploaded_file_url = fs.url(filename)
    return render(request, 'tools/restore.html', {
        'uploaded_file_url': uploaded_file_url
    })
  return render(request, 'tools/restore.html')
  
def logout_and_redirect(request):
  logout(request)
  return redirect('/')
