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

from ua_parser import user_agent_parser
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User as dbuser
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import ListView
from access.c_access import access
from tools.l_tools import djconf
from tools.tokens import checktoken
from tf_workers.models import school
from users.models import archive
from .models import event, event_frame

archivepath = djconf.getconfig('archivepath', 'data/archive/')

@login_required
def events(request, schoolnr):
  if (((schoolnr > 1) or (request.user.is_superuser)) 
      and (access.check('S', schoolnr, request.user, 'R'))):
    template = loader.get_template('eventers/events.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'events' : event.objects.filter(school_id=schoolnr, xmax__gt=0).order_by('-id'),
      'debug' : settings.DEBUG,
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
      'school' : school.objects.get(id=schoolnr),
      'user' : request.user,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

@login_required
def oneevent(request, schoolnr, eventnr):
  myevent = event.objects.get(id=eventnr)
  if ((myevent.school.id == schoolnr) 
      and ((schoolnr > 1) or (request.user.is_superuser))
      and access.check('S', schoolnr, request.user, 'R')):
    length_in_seconds = round(myevent.end.timestamp() - myevent.start.timestamp())
    length = str(length_in_seconds // 60)+':'
    seconds = str(length_in_seconds % 60)
    if len(seconds) == 1:
      seconds = '0'+seconds
    length += seconds
    frames = event_frame.objects.filter(event_id=eventnr)
    for item in frames:
      item.name = item.name.replace('/', '$', 2)
    useragent = user_agent_parser.Parse(request.META['HTTP_USER_AGENT'])
    is_android = (useragent['os']['family'] == 'Android') or (useragent['user_agent']['family'] == 'Samsung Internet') 
    template = loader.get_template('eventers/oneevent.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'is_android' : is_android,
      'uastring' : useragent['string'],
      'os' : useragent['os']['family'],
      'browser' : useragent['user_agent']['family'],
      'event' : event.objects.get(id=eventnr),
      'frames' : frames,
      'debug' : settings.DEBUG,
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
      'school' : school.objects.get(id=schoolnr),
      'length' : length,
      'user' : request.user,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

def eventjpg(request, eventnr, tokennr=None, token=None):
  myevent = event.objects.get(id=eventnr)
  if request.user.id is None:
    if (tokennr and token):
      go_on = checktoken((tokennr, token), 'EVR', eventnr)
    else:
      go_on = False
  else:
    myschool = myevent.school.id
    go_on = access.check('S', myschool, request.user, 'R')
  if not go_on:
    return(HttpResponse('No Access'))
  filename = (myevent.videoclip + '.jpg')
  filepath = djconf.getconfig('recordingspath', 'data/recordings/') + filename
  with open(filepath, "rb") as f:
    return HttpResponse(f.read(), content_type="image/jpeg")

def eventmp4(request, archivenr=0, eventnr=0, tokennr=None, token=None):
  if eventnr:
    myevent = event.objects.get(id=eventnr)
    if request.user.id is None:
      if (tokennr and token):
        go_on = checktoken((tokennr, token), 'EVR', eventnr)
      else:
        go_on = False
    else:
      myschool = myevent.school.id
      go_on = access.check('S', myschool, request.user, 'R')
  elif archivenr:
    archiveline = archive.objects.get(id = archivenr)
    userset = set(dbuser.objects.filter(archive=archiveline))
    go_on = (request.user in userset)
  else:
    go_on = False    
  if not go_on:
    return(HttpResponse('No Access'))
  if eventnr:  
    filename = (myevent.videoclip + '.mp4')
    filepath = djconf.getconfig('recordingspath', 'data/recordings/') + filename
  elif archivenr:
    filepath = (archivepath + 'videos/' + archiveline.name + '.mp4')
  with open(filepath, "rb") as f:
    result = HttpResponse(f.read(), content_type="video/mp4")
    return(result)

def eventwebm(request, archivenr=0, eventnr=0, tokennr=None, token=None):
  if eventnr:
    myevent = event.objects.get(id=eventnr)
    if request.user.id is None:
      if (tokennr and token):
        go_on = checktoken((tokennr, token), 'EVR', eventnr)
      else:
        go_on = False
    else:
      myschool = myevent.school.id
      go_on = access.check('S', myschool, request.user, 'R')
  elif archivenr:
    archiveline = archive.objects.get(id = archivenr)
    userset = set(dbuser.objects.filter(archive=archiveline))
    go_on = (request.user in userset)
  else:
    go_on = False    
  if not go_on:
    return(HttpResponse('No Access'))
  if eventnr:  
    filename = (myevent.videoclip + '.webm')
    filepath = djconf.getconfig('recordingspath', 'data/recordings/') + filename
  elif archivenr:
    filepath = (archivepath + 'videos/' + archiveline.name + '.webm')
  with open(filepath, "rb") as f:
    result = HttpResponse(f.read(), content_type="video/webm")
    return(result)
