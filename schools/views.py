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

from PIL import Image
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from access.c_access import access
from tools.l_tools import djconf
from tools.c_tools import c_convert
from streams.models import stream
from tf_workers.models import school
from users.models import userinfo
from eventers.models import event

@login_required
def images(request, schoolnr):
  if access.check('S', schoolnr, request.user, 'R'):
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
  if access.check('S', schoolnr, request.user, 'R'):
    template = loader.get_template('schools/classroom.html')
    try:
      myuserinfo = userinfo.objects.get(user = request.user.id)
    except userinfo.DoesNotExist:
      myuserinfo = userinfo(user_id=request.user.id, school_id=schoolnr, counter=0)
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'userinfo' : myuserinfo,
      'school' : school.objects.get(id=schoolnr),
      'events' : event.objects.filter(school_id=schoolnr, done=False, xmax__gt=0),
      'debug' : settings.DEBUG,
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
      'user' : request.user,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

#@login_required
#no login when called from email
#schoolnr = 0 --> from school directory
def getbmp(request, schoolnr, name, outtype, xycontained, x, y): 
  if schoolnr == 0:
    name = name.replace('$', '/', 2)
    filepath = djconf.getconfig('schoolframespath', 'data/schoolframes/') + name
  else:
    line = school.objects.get(id=schoolnr)
    filepath = line.dir + 'frames/' + name
  with open(filepath, "rb") as f:
    myframe = c_convert(f.read(), 2, outtype, xycontained, x, y)
  return HttpResponse(myframe, content_type="image/jpeg")

@login_required
#schoolnr = 0 --> from school directory
def getbigbmp(request, schoolnr, name): 
  template = loader.get_template('schools/bigbmp.html')
  context = {
    'school' : schoolnr,
    'name' : name,
  }
  return(HttpResponse(template.render(context)))
