# schools/views.py
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
import os
import threading
from time import time
from shutil import rmtree
from glob import glob
from ua_parser import user_agent_parser
from pathlib import Path
from zipfile import ZipFile
from functools import wraps
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as dbuser
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.views.decorators.cache import cache_control
from django.db import connection
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

datapath = djconf.getconfig('datapath', 'data/')
schoolframespath = djconf.getconfig('schoolframespath', datapath + 'schoolframes/')
archivepath = djconf.getconfig('archivepath', datapath + 'archive/')
is_public_server = djconf.getconfigbool('is_public_server', False)
crypter_dict = {}
_school_cache = {}   # school_nr -> (timestamp, schoolline)
_access_cache = {}   # (user_id, school_nr) -> (timestamp, bool)
_CACHE_TTL = 60.0
os.makedirs('temp/upload', exist_ok=True)
os.makedirs('temp/unpack', exist_ok=True)
_getbmp_sem = threading.BoundedSemaphore(8)

def limit_concurrency(sem, timeout = 15.0):
  def deco(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
      # Release any connection opened by middleware before we block:
      connection.close()
      if not sem.acquire(timeout = timeout):
        return(HttpResponse('Busy', status = 503))
      try:
        return(func(*args, **kwargs))
      finally:
        sem.release()
    return(wrapper)
  return(deco)

@login_required
def images(request, schoolnr):
  if access.check('S', schoolnr, request.user, 'W'):
    myschool = school.objects.get(id=schoolnr)
    template = loader.get_template('schools/images.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
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
def imexport(request, schoolnr):
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
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
    return render(request, 'schools/imexport.html', context)

#mode == 0: Classroom Dir, mode == 1: Model Dir
#mode == 2: Archive Image, mode == 3: Archive video 
@cache_control(private = True, max_age = 86400)
@limit_concurrency(_getbmp_sem)
def getbmp(request, mode, framenr, outtype, xycontained, x, y, 
    tokennr=None, token=None): 
  global crypter_dict
  if mode == 0:
    event_frame_line = event_frame.objects.select_related(
      'event__camera').get(id = framenr)
    crypt = event_frame_line.encrypted
    filepath = schoolframespath + event_frame_line.name
    stream_nr = event_frame_line.event.camera.id
    if crypt:
      crypter_dict.setdefault(
        stream_nr, 
        l_crypt(key = event_frame_line.event.camera.crypt_key), 
      )
  elif mode == 1:
    trainframe_line = trainframe.objects.get(id = framenr)
    school_nr = trainframe_line.school
    # School rows rarely change - cache them per process with a TTL:
    cached = _school_cache.get(school_nr)
    if cached is None or cached[0] + _CACHE_TTL < time():
      schoolline = school.objects.get(id = school_nr)
      _school_cache[school_nr] = (time(), schoolline)
    else:
      schoolline = cached[1]
    #trainframe_line = trainframe.objects.get(id = framenr)
    #school_nr = trainframe_line.school
    #schoolline = school.objects.get(id = school_nr)
    filepath_raw = schoolline.dir + '*****/' + trainframe_line.name
    filepath = filepath_raw.replace('*****', 'frames', 1)
    if not os.path.exists(filepath):
      filepath = filepath_raw.split("*****/", 1)[0]
      filepath = filepath + 'coded/' + '224x224/' + trainframe_line.name[:-3] + 'cod'
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
      go_on = access.check('C', stream_nr, request.user, 'R')
    elif mode == 1:
      # Same user hits this ~100x per gallery page - cache the result:
      cache_key = (request.user.id, school_nr)
      cached = _access_cache.get(cache_key)
      if cached is None or cached[0] + _CACHE_TTL < time():
        go_on = access.check('S', school_nr, request.user, 'R')
        _access_cache[cache_key] = (time(), go_on)
      else:
        go_on = cached[1]
    else:
      go_on = (request.user in userset)
  if not go_on:
    return(HttpResponse('No Access'))
  # All DB work is done - release the connection slot before the
  # expensive file IO and image conversion:
  connection.close()
  with open(filepath, "rb") as f:
    image_data = f.read()
  if crypt: 
    myframe = c_convert(image_data, typein=2, typeout=outtype, xycontained=xycontained, 
      xout=x, yout=y, incrypt=crypter_dict[stream_nr]) 
  else:
    myframe = c_convert(image_data, typein=2, typeout=outtype, xycontained=xycontained, 
      xout=x, yout=y)  
  return HttpResponse(myframe, content_type="image/bmp")

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
    'is_android' : is_android,
    'os' : useragent['os']['family'],
    'browser' : useragent['user_agent']['family'],
    'linenr' : linenr,
    'tokennr' : tokennr,
    'token' : token,
    'do_webm' : djconf.getconfigbool('do_webm', False),
  }
  return(HttpResponse(template.render(context)))
