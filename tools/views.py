from django.conf import settings
from django.views.generic.base import TemplateView
from django.shortcuts import render
from streams.models import stream
from access.c_access import access
from tf_workers.models import school
from tools.l_tools import djconf

class health(TemplateView):
  template_name = 'tools/health.html'


  def get_context_data(self, **kwargs):
    camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', self.request.user, 'R')
    detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', self.request.user, 'R')
    eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', self.request.user, 'R')
    schoollist = access.filter_items(school.objects.filter(active=True), 'S', self.request.user, 'R')
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'camlist' : camlist,
      'detectorlist' : detectorlist,
      'eventerlist' : eventerlist,
      'schoollist' : schoollist,
      'recordingspath' : djconf.getconfig('recordingspath', 'data/recordings/'),
      'schoolframespath' : djconf.getconfig('schoolframespath', 'data/schoolframes/')
    })
    return context
