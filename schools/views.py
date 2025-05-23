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

import os
from shutil import rmtree
from glob import glob
from ua_parser import user_agent_parser
from zipfile import ZipFile
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as dbuser
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from camai.c_settings import safe_import
from access.c_access import access
from tools.l_tools import djconf
from tools.c_tools import c_convert
from tools.tokens import checktoken
from tools.l_crypt import l_crypt
from streams.models import stream
from tf_workers.models import school
from users.models import archive
from users.userinfo import free_quota
from eventers.models import event, event_frame
from trainers.models import trainframe

emulatestatic = safe_import('emulatestatic') 


datapath = djconf.getconfig('datapath', 'data/')
schoolframespath = djconf.getconfig('schoolframespath', datapath + 'schoolframes/')
archivepath = djconf.getconfig('archivepath', datapath + 'archive/')
is_public_server = djconf.getconfigbool('is_public_server', False)
crypter_dict = {}
os.makedirs('temp/upload', exist_ok=True)
os.makedirs('temp/unpack', exist_ok=True)

@login_required
def images(request, schoolnr):
  if access.check('S', schoolnr, request.user, 'W'):
    myschool = school.objects.get(id=schoolnr)
    template = loader.get_template('schools/images.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'schoolnr' : schoolnr,
      'schoolname' : myschool.name,
      'user' : request.user,
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

@login_required
def classroom(request, streamnr):
  myschool = stream.objects.get(id=streamnr).eve_school
  if access.check('S', myschool.id, request.user, 'W'):
    mystream = stream.objects.get(id=streamnr)
    template = loader.get_template('schools/classroom.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'school' : myschool,
      'stream' : mystream,
      'debug' : settings.DEBUG,
      'may_write_stream' : access.check('C', streamnr, request.user, 'W'),
      'may_write_school' : access.check('S', myschool.id, request.user, 'W'),
      'stream' : mystream,
      'user' : request.user,
      'has_quota' : free_quota(mystream.creator) > 0,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

@login_required
def upload_file(request, schoolnr):
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'emulatestatic' : emulatestatic,
    'school' : schoolnr,
  }
  if request.method == 'POST' and request.FILES['file']:
    
    uploaded_file = request.FILES['file']
    fs = FileSystemStorage(location='temp/upload')
    filename = fs.save(uploaded_file.name, uploaded_file)
    file_path = fs.path(filename)
    if os.path.exists('temp/unpack/' + filename):
      rmtree('temp/unpack/' + filename)
    os.makedirs('temp/unpack/' + filename)
    with ZipFile(file_path, 'r') as zip_ref:
      zip_ref.extractall('temp/unpack/' + filename) 
    zipresult = glob('temp/unpack/' + filename + '/*')
    os.remove(file_path)
    context['file_number'] = len(zipresult)
    context['file_name'] = uploaded_file.name
    return render(request, 'schools/upload_success.html', context)
  else:
    return render(request, 'schools/upload_file.html', context)

#mode == 0: Classroom Dir, mode == 1: Model Dir
#mode == 2: Archive Image, mode == 3: Archive video 
def getbmp(request, mode, framenr, outtype, xycontained, x, y, tokennr=None, token=None): 
  global crypter_dict
  if mode == 0:
    frameline = event_frame.objects.get(id = framenr)
    eventline = frameline.event
    streamline = eventline.camera
    if (crypt := frameline.encrypted):
      if not streamline.id in crypter_dict:
        crypter_dict[streamline.id] = l_crypt(key=streamline.crypt_key)
    if (
        is_public_server 
        and request.user.is_superuser 
        and request.user.id != streamline.creator.id
        and crypt
    ):   
      filepath = 'camai/static/camai/git/img/privacy.jpg'
    else:
      filepath = schoolframespath + frameline.name
  elif mode == 1:
    frameline = trainframe.objects.get(id = framenr)
    schoolline = school.objects.get(id = frameline.school)
    filepath = schoolline.dir + 'frames/' + frameline.name
    if not os.path.exists(filepath):
      filepath = schoolline.dir + 'coded/' + '224x224/' + frameline.name[:-3] + 'cod'
      filepath = filepath[:-3]+'cod'
    crypt = False
  elif mode == 2:
    frameline = archive.objects.get(id = framenr)
    filepath = archivepath + 'frames/' + frameline.name
    userset = set(dbuser.objects.filter(archive=frameline))
    crypt = False
  elif mode == 3:
    frameline = archive.objects.get(id = framenr)
    filepath = archivepath + 'videos/' + frameline.name + '.jpg'
    userset = set(dbuser.objects.filter(archive=frameline))
    crypt = False
  if request.user.id is None:
    if mode == 0:
      if (tokennr and token):
        go_on = checktoken((tokennr, token), 'EVR', eventline.id)
      else:
        go_on = False
    else:
      go_on = False
  else:
    if mode == 0:
      go_on = access.check('C', streamline.id, request.user, 'R')
    elif mode == 1:
      go_on = access.check('S', schoolline.id, request.user, 'R')
    else:
      go_on = (request.user in userset)
  if not go_on:
    return(HttpResponse('No Access'))
  with open(filepath, "rb") as f:
    if crypt: 
      if (is_public_server 
        and request.user.is_superuser
        and request.user.id != streamline.creator.id
      ):
        myframe = c_convert(f.read(), typein=3, typeout=outtype, xycontained=xycontained, 
          xout=x, yout=y)
      else:  
        myframe = c_convert(f.read(), typein=2, typeout=outtype, xycontained=xycontained, 
          xout=x, yout=y, incrypt=crypter_dict[streamline.id]) 
    else:
      myframe = c_convert(f.read(), typein=2, typeout=outtype, xycontained=xycontained, 
        xout=x, yout=y)  
          
  return HttpResponse(myframe, content_type="image/jpeg")

#schoolnr = 0 --> from classroom directory
def getbigbmp(request, mode, framenr, tokennr=0, token=''): 
  if mode == 0:
    frameline = event_frame.objects.get(id = framenr)
    eventline = frameline.event
    schoolline = eventline.school
  elif mode == 1:
    frameline = trainframe.objects.get(id = framenr)
    schoolline = school.objects.get(id = frameline.school)
  elif mode in {2, 3}:
    frameline = archive.objects.get(id = framenr)
    userset = set(dbuser.objects.filter(archive=frameline))
  if request.user.id is None:
    if mode == 0:
      if (tokennr and token):
        go_on = checktoken((tokennr, token), 'EVR', eventline.id)
      else:
        go_on = False
    else:
      go_on = False
  else:
    if mode in {0, 1}:
      go_on = access.check('S', schoolline.id, request.user, 'R')
    elif mode in {2, 3}:
      go_on = (request.user in userset)
  if not go_on:
    return(HttpResponse('No Access'))
  template = loader.get_template('schools/bigbmp.html')
  context = {
    'mode' : mode,
    'framenr' : framenr,
    'tokennr' : tokennr,
    'token' : token,
  }
  return(HttpResponse(template.render(context)))

def getbigmp4(request, archivenr=0, eventnr=0, tokennr=None, token=None):
  if eventnr:
    myevent = event.objects.get(id=eventnr)
    if (tokennr and token):
      go_on = checktoken((tokennr, token), 'EVR', eventnr)
    else:
      go_on = False
    linenr = eventnr  
  elif archivenr:
    archiveline = archive.objects.get(id = archivenr)
    userset = set(dbuser.objects.filter(archive=archiveline))
    go_on = (request.user in userset)
    linenr = archivenr
  else:
    go_on = False    
  if not go_on:
    return(HttpResponse('No Access'))
  useragent = user_agent_parser.Parse(request.META['HTTP_USER_AGENT'])
  is_android = (useragent['os']['family'] == 'Android') or (useragent['user_agent']['family'] == 'Samsung Internet') 
  template = loader.get_template('schools/bigmp4.html')
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'emulatestatic' : emulatestatic,
    'is_android' : is_android,
    'os' : useragent['os']['family'],
    'browser' : useragent['user_agent']['family'],
    'linenr' : linenr,
    'tokennr' : tokennr,
    'token' : token,
    'do_webm' : djconf.getconfigbool('do_webm', False),
  }
  return(HttpResponse(template.render(context)))
