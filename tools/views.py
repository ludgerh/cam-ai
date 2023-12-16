# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
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

import json
#from pprint import pprint
from requests import get as rget
from django.conf import settings
from django.views.generic.base import TemplateView
from django.shortcuts import render
from django.http import HttpResponse, FileResponse, HttpResponseRedirect
from streams.models import stream
from users.models import userinfo
from access.c_access import access
from tf_workers.models import school, worker
from tools.l_tools import djconf
from .models import camurl
from .forms import UploadFileForm

class health(TemplateView):
  template_name = 'tools/health.html'

  def get_context_data(self, **kwargs):
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    templist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    schoollist = []
    for item in templist:
      if (item.id > 1) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
    context = super().get_context_data(**kwargs)
    datapath = djconf.getconfig('datapath', 'data/')
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'recordingspath' : djconf.getconfig('recordingspath', datapath + 'recordings/'),
      'schoolframespath' : djconf.getconfig('schoolframespath', 
        datapath + 'schoolframes/')
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))

class dbcompression(TemplateView):
  template_name = 'tools/dbcompression.html'

  def get_context_data(self, **kwargs):
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    templist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    schoollist = []
    for item in templist:
      if (item.id > 1) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
    context = super().get_context_data(**kwargs)
    datapath = djconf.getconfig('datapath', 'data/')
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'recordingspath' : djconf.getconfig('recordingspath', datapath + 'recordings/'),
      'schoolframespath' : djconf.getconfig('schoolframespath', 
        datapath + 'schoolframes/')
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))

class scan_cams(TemplateView):
  template_name = 'tools/scan_cams.html'

  def get_context_data(self, **kwargs):
    streamlimit = userinfo.objects.get(user = self.request.user.id).allowed_streams
    streamcount = stream.objects.filter(creator = self.request.user.id, active = True, ).count()
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    templist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    schoollist = []
    for item in templist:
      if (item.id > 1) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'streamlimit' : streamlimit,
      'streamcount' : streamcount,
      'mayadd' : (streamlimit > streamcount),
      'is_public_server' : djconf.getconfigbool('is_public_server', False),
    })
    return context

class inst_cam(TemplateView):
  template_name = 'tools/inst_cam.html'

  def get_context_data(self, **kwargs):
    streamlimit = userinfo.objects.get(user = self.request.user.id).allowed_streams
    streamcount = stream.objects.filter(creator = self.request.user.id, active = True, ).count()
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    templist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    schoollist = []
    for item in templist:
      if (item.id > 1) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
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
      'ipaddress' : kwargs['ip'],
      'ports' : json.loads(kwargs['ports']),
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
    templist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    schoollist = []
    for item in templist:
      if (item.id > 1) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
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
    templist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    schoollist = []
    for item in templist:
      if (item.id > 1) or (not worker.objects.get(id=1).use_websocket):
        schoollist.append(item)
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

class shutdown(TemplateView):
  template_name = 'tools/shutdown.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
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
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'new_version' : response['tag_name'],
      'zip_url' : response['zipball_url']
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
      
class backup(TemplateView):
  template_name = 'tools/backup.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
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
    filename = '../temp/backup/backup.zip'
    sourcefile = open(filename, 'rb')
    return FileResponse(sourcefile)
  else:
    return(HttpResponse('No Access.'))
      
#class restore(TemplateView):
#  template_name = 'tools/restore.html'

#  def get_context_data(self, **kwargs):
#    context = super().get_context_data(**kwargs)
#    context.update({
#      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
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
