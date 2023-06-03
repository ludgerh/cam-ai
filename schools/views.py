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

#from PIL import Image
from ua_parser import user_agent_parser
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from access.c_access import access
from tools.l_tools import djconf
from tools.c_tools import c_convert
from tools.tokens import checktoken
from streams.models import stream
from tf_workers.models import school
from users.models import userinfo
from eventers.models import event, event_frame
from trainers.models import trainframe

@login_required
def images(request, schoolnr):
  if (((schoolnr > 1) or (request.user.is_superuser)) 
      and (access.check('S', schoolnr, request.user, 'R'))):
    myschool = school.objects.get(pk = schoolnr)
    template = loader.get_template('schools/images.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
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
def classroom(request, schoolnr):
  if (((schoolnr > 1) or (request.user.is_superuser)) 
      and (access.check('S', schoolnr, request.user, 'R'))):
    template = loader.get_template('schools/classroom.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'school' : school.objects.get(id=schoolnr),
      'events' : event.objects.filter(school_id=schoolnr, done=False, xmax__gt=0),
      'debug' : settings.DEBUG,
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
      'user' : request.user,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

#schoolnr = 0 --> from classroom directory
def getbmp(request, mode, framenr, outtype, xycontained, x, y, tokennr=None, token=None): 
  if mode == 0:
    frameline = event_frame.objects.get(id = framenr)
    eventline = frameline.event
    schoolline = eventline.school
    filepath = djconf.getconfig('schoolframespath', 'data/schoolframes/') + frameline.name
  else:
    frameline = trainframe.objects.get(id = framenr)
    schoolline = school.objects.get(id = frameline.school)
    filepath = schoolline.dir + 'frames/' + frameline.name
  if request.user.id is None:
    if mode == 0:
      if (tokennr and token):
        go_on = checktoken((tokennr, token), 'EVR', eventline.id)
      else:
        go_on = False
    else:
      go_on = False
  else:
    go_on = access.check('S', schoolline.id, request.user, 'R')
  if not go_on:
    return(HttpResponse('No Access'))

  with open(filepath, "rb") as f:
    myframe = c_convert(f.read(), typein=2, typeout=outtype, xycontained=xycontained, xout=x, yout=y)
  return HttpResponse(myframe, content_type="image/jpeg")

#schoolnr = 0 --> from classroom directory
def getbigbmp(request, mode, framenr, tokennr=0, token=''): 
  if mode == 0:
    frameline = event_frame.objects.get(id = framenr)
    eventline = frameline.event
    schoolline = eventline.school
  else:
    frameline = trainframe.objects.get(id = framenr)
    schoolline = school.objects.get(id = frameline.school)
  if request.user.id is None:
    if mode == 0:
      if (tokennr and token):
        go_on = checktoken((tokennr, token), 'EVR', eventline.id)
      else:
        go_on = False
    else:
      go_on = False
  else:
    go_on = access.check('S', schoolline.id, request.user, 'R')
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

def getbigmp4(request, eventnr, tokennr=None, token=None):
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
  useragent = user_agent_parser.Parse(request.META['HTTP_USER_AGENT'])
  is_android = (useragent['os']['family'] == 'Android') or (useragent['user_agent']['family'] == 'Samsung Internet') 
  template = loader.get_template('schools/bigmp4.html')
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
    'is_android' : is_android,
    'uastring' : useragent['string'],
    'os' : useragent['os']['family'],
    'browser' : useragent['user_agent']['family'],
    'eventnr' : eventnr,
    'tokennr' : tokennr,
    'token' : token,
  }
  return(HttpResponse(template.render(context)))
