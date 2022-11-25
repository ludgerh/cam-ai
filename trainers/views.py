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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from access.c_access import access
from tf_workers.models import school
from schools.c_schools import get_taglist
from tools.l_tools import djconf
from .models import fit

@login_required
def trainer(request, schoolnr):
  if access.check('S', schoolnr, request.user, 'R'):
    myschool = school.objects.get(pk = schoolnr)
    template = loader.get_template('trainers/trainer.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'schoolnr' : schoolnr,
      'schoolname' : myschool.name,
      'taglist' : get_taglist(schoolnr),
      'user' : request.user,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

def epochs(request, schoolnr, fitnr):
  if access.check('S', schoolnr, request.user, 'R'):
    template = loader.get_template('trainers/epochs.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'user' : request.user,
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'fitnr' : fitnr,
      'schoolnr' : schoolnr,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

def dashboard(request, schoolnr):
  if access.check('S', schoolnr, request.user, 'R'):
    myschool = school.objects.get(pk = schoolnr)
    template = loader.get_template('trainers/dashboard.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'user' : request.user,
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'school' : myschool,
      'schoolnr' : schoolnr,
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))
