from django.shortcuts import render
from django.template import loader
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from access.c_access import access
from streams.models import stream
from tf_workers.models import school
from tools.l_tools import djconf


@login_required
def index(request, mode='C'):
  camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', request.user, 'R')
  detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', request.user, 'R')
  eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', request.user, 'R')
  schoollist = access.filter_items(school.objects.filter(active=True), 'S', request.user, 'R')
  template = loader.get_template('index/index.html')
  context = {
    'version' : djconf.getconfig('version', 'X.Y.Z'),
    'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
    'debug' : settings.DEBUG,
    'mode' : mode,
    'camlist' : camlist,
    'detectorlist' : detectorlist,
    'eventerlist' : eventerlist,
    'schoollist' : schoollist,
    'user' : request.user,
  }
  return(HttpResponse(template.render(context)))
