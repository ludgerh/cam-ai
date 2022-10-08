from PIL import Image
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from access.c_access import access
from tools.l_tools import djconf
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
    }
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))

#@login_required
#no login when called from email
#schoolnr = 0 --> from school directory
def getbmp(request, schoolnr, name): 
  if schoolnr == 0:
    name = name.replace('$', '/', 2)
    filepath = djconf.getconfig('schoolframespath', 'data/schoolframes/') + name
  else:
    line = school.objects.get(id=schoolnr)
    filepath = line.dir + 'frames/' + name
  try:
    with open(filepath, "rb") as f:
      return HttpResponse(f.read(), content_type="image/jpeg")
  except IOError:
    red = Image.new('RGB', (1, 1), (255,0,0))
    response = HttpResponse(content_type="image/jpeg")
    red.save(response, "JPEG")
    return response

@login_required
#schoolnr = 0 --> from school directory
def getbigbmp(request, schoolnr, name): 
  template = loader.get_template('schools/bigbmp.html')
  context = {
    'school' : schoolnr,
    'name' : name,
  }
  return(HttpResponse(template.render(context)))
