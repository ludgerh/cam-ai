from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from access.c_access import access
from streams.models import stream
from streams.c_streams import streams
from tf_workers.models import school
from .forms import CamForm , DetectorForm, EventerForm
from tools.l_tools import djconf


def onecam(request, camnr):
  if access.check('C', camnr, request.user, 'R'):
    dbline = stream.objects.get(id=camnr)
    mycam = streams[camnr].mycam
    myurl = '/oneitem/cam/'
    if request.method == 'POST':
      form = CamForm(request.POST)
      if form.is_valid():
        streams[camnr].dbline.cam_fpslimit = form.cleaned_data['cam_fpslimit']
        streams[camnr].dbline.cam_feed_type = form.cleaned_data['cam_feed_type']
        streams[camnr].dbline.cam_url = form.cleaned_data['cam_url']
        streams[camnr].dbline.cam_repeater = form.cleaned_data['cam_repeater']
        streams[camnr].dbline.save(update_fields=[
          'cam_fpslimit', 
          'cam_feed_type',
          'cam_url',
          'cam_repeater',
        ])
        mycam.inqueue.put(('reset_cam',))
        return HttpResponseRedirect(myurl+str(camnr)+'/')
    else:
      form = CamForm(initial={
        'cam_fpslimit' : dbline.cam_fpslimit,
        'cam_feed_type' : dbline.cam_feed_type,
        'cam_url' : dbline.cam_url,
        'cam_repeater' : dbline.cam_repeater,
      })
      camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', request.user, 'R')
      detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', request.user, 'R')
      eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', request.user, 'R')
      schoollist = access.filter_items(school.objects.filter(active=True), 'S', request.user, 'R')
      context = {
        'version' : djconf.getconfig('version', 'X.Y.Z'),
        'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
        'debug' : settings.DEBUG,
        'dbline' : dbline,
        'camlist' : camlist,
        'detectorlist' : detectorlist,
        'eventerlist' : eventerlist,
        'schoollist' : schoollist,
        'myurl' : myurl,
        'form' : form,
        'may_write' : access.check('C', camnr, request.user, 'W'),
        'user' : request.user,
      }
    return(render(request, 'oneitem/onecam.html', context))
  else:
    return(HttpResponse('No Access'))

def onedetector(request, detectornr):
  if access.check('D', detectornr, request.user, 'R'):
    dbline = stream.objects.get(id=detectornr)
    mydetector = streams[detectornr].mydetector
    myurl = '/oneitem/detector/'
    if request.method == 'POST':
      form = DetectorForm(request.POST)
      if form.is_valid():
        streams[detectornr].dbline.det_fpslimit = form.cleaned_data['det_fpslimit']
        streams[detectornr].dbline.det_threshold = form.cleaned_data['det_threshold']
        streams[detectornr].dbline.det_backgr_delay = form.cleaned_data['det_backgr_delay']
        streams[detectornr].dbline.det_dilation = form.cleaned_data['det_dilation']
        streams[detectornr].dbline.det_erosion = form.cleaned_data['det_erosion']
        streams[detectornr].dbline.det_max_size = form.cleaned_data['det_max_size']
        streams[detectornr].dbline.det_max_rect = form.cleaned_data['det_max_rect']
        streams[detectornr].dbline.save(update_fields=[
          'det_fpslimit', 
          'det_threshold',
          'det_backgr_delay',
          'det_dilation',
          'det_erosion',
          'det_max_size',
          'det_max_rect',
        ])
        return HttpResponseRedirect(myurl+str(detectornr)+'/')
    else:
      form = DetectorForm(initial={
        'det_fpslimit' : dbline.det_fpslimit,
        'det_threshold' : dbline.det_threshold,
        'det_backgr_delay' : dbline.det_backgr_delay,
        'det_dilation' : dbline.det_dilation,
        'det_erosion' : dbline.det_erosion,
        'det_max_size' : dbline.det_max_size,
        'det_max_rect' : dbline.det_max_rect,
      })
      camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', request.user, 'R')
      detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', request.user, 'R')
      eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', request.user, 'R')
      schoollist = access.filter_items(school.objects.filter(active=True), 'S', request.user, 'R')
      context = {
        'version' : djconf.getconfig('version', 'X.Y.Z'),
        'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
        'debug' : settings.DEBUG,
        'dbline' : dbline,
        'camlist' : camlist,
        'detectorlist' : detectorlist,
        'eventerlist' : eventerlist,
        'schoollist' : schoollist,
        'myurl' : myurl,
        'form' : form,
        'may_write' : access.check('D', detectornr, request.user, 'W'),
        'user' : request.user,
      }
    return(render(request, 'oneitem/onedetector.html', context))
  else:
    return(HttpResponse('No Access'))

def oneeventer(request, eventernr):
  if access.check('E', eventernr, request.user, 'R'):
    dbline = stream.objects.get(id=eventernr)
    myeventer = streams[eventernr].mydetector.myeventer
    myurl = '/oneitem/eventer/'
    if request.method == 'POST':
      form = EventerForm(request.POST)
      if form.is_valid():
        streams[eventernr].dbline.eve_fpslimit = form.cleaned_data['eve_fpslimit']
        streams[eventernr].dbline.eve_margin = form.cleaned_data['eve_margin']
        streams[eventernr].dbline.eve_event_time_gap = form.cleaned_data['eve_event_time_gap']
        streams[eventernr].dbline.eve_school = form.cleaned_data['eve_school']
        streams[eventernr].dbline.eve_alarm_email = form.cleaned_data['eve_alarm_email']
        streams[eventernr].dbline.save(update_fields=[
          'eve_fpslimit', 
          'eve_margin',
          'eve_event_time_gap',
          'eve_school',
          'eve_alarm_email',
        ])
        return HttpResponseRedirect(myurl+str(eventernr)+'/')
    else:
      form = EventerForm(initial={
        'eve_fpslimit' : dbline.eve_fpslimit,
        'eve_margin' : dbline.eve_margin,
        'eve_event_time_gap' : dbline.eve_event_time_gap,
        'eve_school' : dbline.eve_school,
        'eve_alarm_email' : dbline.eve_alarm_email,
      })
      camlist = access.filter_items(stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', request.user, 'R')
      detectorlist = access.filter_items(stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', request.user, 'R')
      eventerlist = access.filter_items(stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', request.user, 'R')
      schoollist = access.filter_items(school.objects.filter(active=True), 'S', request.user, 'R')
      context = {
        'version' : djconf.getconfig('version', 'X.Y.Z'),
        'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
        'debug' : settings.DEBUG,
        'dbline' : dbline,
        'camlist' : camlist,
        'detectorlist' : detectorlist,
        'eventerlist' : eventerlist,
        'schoollist' : schoollist,
        'myurl' : myurl,
        'form' : form,
        'may_write' : access.check('E', eventernr, request.user, 'W'),
        'user' : request.user,
      }
    return(render(request, 'oneitem/oneeventer.html', context))
  else:
    return(HttpResponse('No Access'))
