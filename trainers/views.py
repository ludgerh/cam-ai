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

from django.contrib.auth.decorators import login_required
from django.template import loader
from django.conf import settings
from django.http import HttpResponse, FileResponse
from camai.c_settings import safe_import
from access.c_access import access
from tf_workers.models import school
from schools.c_schools import get_taglist
from tools.l_tools import djconf
from tools.tokens import checktoken
from .models import model_type, fit

emulatestatic = safe_import('emulatestatic') 

@login_required
def trainer(request, schoolnr):
  if (((schoolnr > 1) or (request.user.is_superuser)) 
      and (access.check('S', schoolnr, request.user, 'R'))):
    myschool = school.objects.get(pk = schoolnr)
    template = loader.get_template('trainers/trainer.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
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
  if (((schoolnr > 1) or (request.user.is_superuser)) 
      and (access.check('S', schoolnr, request.user, 'R'))):
    template = loader.get_template('trainers/epochs.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'user' : request.user,
      'emulatestatic' : emulatestatic,
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
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'school' : myschool,
      'schoolnr' : schoolnr,
      'model_types' : model_type.objects.all(),
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
      'show_all_options' : request.user.is_superuser,
      'delegation_level' : myschool.delegation_level,
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))
    
def downmodel(request, schoolnr, tokennr, token, model_type = 'K', fit_nr = None): 
  if checktoken((tokennr, token), 'MOD', schoolnr):
    if fit_nr:
      fitline = fit.objects.get(id=fit_nr)
    if fitline.status == 'Done':    
      myschool = school.objects.get(id = schoolnr)
      filename = myschool.dir + 'model/'
      if model_type == 'K':
        filename += myschool.model_train_type + '.keras'
      elif model_type == 'L':
        filename += myschool.model_train_type + '.tflite'
      elif model_type == 'Q':
        filename += 'q_' + myschool.model_train_type + '.tflite'
      modelfile = open(filename, 'rb')
      return FileResponse(modelfile)
    elif fitline.status == 'Stopped':   
      return(HttpResponse('Stop!')) 
    else:  
      return(HttpResponse('Wait!'))
  else:
    return(HttpResponse('No Access.'))

