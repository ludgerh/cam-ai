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
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

def epochs(request, schoolnr, fitnr):
  if access.check('S', schoolnr, request.user, 'R'):
    template = loader.get_template('trainers/epochs.html')
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
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
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'school' : myschool,
      'schoolnr' : schoolnr,
      'may_write' : access.check('S', schoolnr, request.user, 'W'),
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))
