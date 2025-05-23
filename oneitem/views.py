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

import asyncio
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth import get_user
from channels.db import database_sync_to_async
from camai.c_settings import safe_import
from access.c_access import access
from streams.models import stream
from globals.c_globals import viewables
from tools.l_tools import djconf
from tools.tokens import checktoken
from tf_workers.models import school
from .forms import CamForm , DetectorForm, EventerForm

emulatestatic = safe_import('emulatestatic') 
    
async def filter_items(model, mode, user, permission):
  queryset = model.objects.filter(active=True)
  if mode == 'C':
    queryset = queryset.filter(cam_mode_flag__gt=0)
  elif mode == 'D':
    queryset = queryset.filter(det_mode_flag__gt=0)
  elif mode == 'E':
    queryset = queryset.filter(eve_mode_flag__gt=0)
  return await database_sync_to_async(access.filter_items)(queryset, mode, user, permission)


class OneCamView(View):

  async def get(self, request, camnr, tokennr=0, token=None):
    user = await database_sync_to_async(get_user)(request)
    if not user.is_authenticated:
      return redirect('/accounts/login/?next=/')
    go_on, may_write = await self.check_access(request, camnr, tokennr, token)
    if not go_on:  
      return HttpResponse('No Access to this ressource!')
    dbline = await stream.objects.aget(id=camnr)
    myurl = '/oneitem/cam/'
    form = CamForm(initial={
      'name': dbline.name,
      'cam_pause': dbline.cam_pause,
      'cam_fpslimit': dbline.cam_fpslimit,
      'cam_ffmpeg_fps': dbline.cam_ffmpeg_fps,
      'cam_url': dbline.cam_url,
      'cam_red_lat': dbline.cam_red_lat,
      'cam_checkdoubles': dbline.cam_checkdoubles,
    })
    context = {
      'version': djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic': emulatestatic,
      'debug': settings.DEBUG,
      'may_write': may_write,
      'tokennr': tokennr,
      'token': token,
      'user': request.user,
      'dbline': dbline,
      'camlist': await filter_items(stream, 'C', request.user, 'R'),
      'detectorlist': await filter_items(stream, 'D', request.user, 'R'),
      'eventerlist': await filter_items(stream, 'E', request.user, 'R'),
      'schoollist': await filter_items(school, 'S', request.user, 'R'),
      'schoollist_write': await filter_items(school, 'S', request.user, 'W'),
      'myurl': myurl,
      'form': form,
    }
    return render(request, 'oneitem/onecam.html', context)
    
  async def post(self, request, camnr, tokennr=0, token=None):
    if not await database_sync_to_async(get_user)(request):
      return JsonResponse({"error": "unauthorized"}, status=401)
    go_on, may_write = await self.check_access(request, camnr, tokennr, token)
    if not go_on:
        return HttpResponse('No Access!')
    dbline = await stream.objects.aget(id=camnr)
    mycam = viewables[camnr]['C']
    myurl = '/oneitem/cam/'
    form = CamForm(request.POST)
    if not form.is_valid():
      return HttpResponse('Invalid form data', status=400)
    dbline.name = form.cleaned_data['name']
    dbline.cam_pause = form.cleaned_data['cam_pause']
    dbline.cam_url = form.cleaned_data['cam_url']
    dbline.cam_fpslimit = form.cleaned_data['cam_fpslimit']
    dbline.cam_ffmpeg_fps = form.cleaned_data['cam_ffmpeg_fps']
    dbline.cam_red_lat = form.cleaned_data['cam_red_lat']
    dbline.cam_checkdoubles = form.cleaned_data['cam_checkdoubles']
    await dbline.asave(update_fields=[
        'name', 'cam_pause', 'cam_fpslimit', 'cam_ffmpeg_fps',
        'cam_url', 'cam_red_lat', 'cam_checkdoubles'
    ])
    await asyncio.to_thread(mycam.inqueue.put, (('reset_cam',)), )
    return HttpResponseRedirect(f'{myurl}{camnr}/')

  async def check_access(self, request, camnr, tokennr, token):
    if await database_sync_to_async(lambda: request.user.is_authenticated)():
      go_on = await access.check_async('C', camnr, request.user, 'R')
      may_write = await access.check_async('C', camnr, request.user, 'W')
    else:
      go_on = (tokennr and token 
        and await database_sync_to_async(checktoken)((tokennr, token), 'CAR', camnr))
      may_write = False
    return go_on, may_write    

class OneDetView(View): 

  async def get(self, request, detnr, tokennr=0, token=None):
    user = await database_sync_to_async(get_user)(request)
    if not user.is_authenticated:
      return redirect('/accounts/login/?next=/')
    go_on, may_write = await self.check_access(request, detnr, tokennr, token)
    if not go_on:  
      return HttpResponse('No Access to this ressource!')
    dbline = await stream.objects.aget(id=detnr)
    await dbline.arefresh_from_db()
    myurl = '/oneitem/detector/'
    form = DetectorForm(initial={
      'det_fpslimit' : dbline.det_fpslimit,
      'det_threshold' : dbline.det_threshold,
      'det_backgr_delay' : dbline.det_backgr_delay,
      'det_dilation' : dbline.det_dilation,
      'det_erosion' : dbline.det_erosion,
      'det_max_size' : dbline.det_max_size,
      'det_max_rect' : dbline.det_max_rect,
      'det_scaledown' : dbline.det_scaledown,
    })
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist': await filter_items(stream, 'C', request.user, 'R'),
      'detectorlist': await filter_items(stream, 'D', request.user, 'R'),
      'eventerlist': await filter_items(stream, 'E', request.user, 'R'),
      'schoollist': await filter_items(school, 'S', request.user, 'R'),
      'schoollist_write': await filter_items(school, 'S', request.user, 'W'),
      'myurl' : myurl,
      'form' : form,
    }
    return render(request, 'oneitem/onedetector.html', context) 
    
  async def post(self, request, detnr, tokennr=0, token=None):
    if not await database_sync_to_async(get_user)(request):
      return JsonResponse({"error": "unauthorized"}, status=401)
    go_on, may_write = await self.check_access(request, detnr, tokennr, token)
    if not go_on:
        return HttpResponse('No Access!')
    dbline = await stream.objects.aget(id=detnr)
    
    await dbline.arefresh_from_db()
    print('11111', dbline.det_fpslimit)
    
    mycam = viewables[detnr]['C']
    myurl = '/oneitem/detector/'
    form = DetectorForm(request.POST)
    if not form.is_valid():
      return HttpResponse('Invalid form data', status=400)
    print(form.cleaned_data)
    dbline.det_fpslimit = form.cleaned_data['det_fpslimit']
    dbline.det_threshold = form.cleaned_data['det_threshold']
    dbline.det_backgr_delay = form.cleaned_data['det_backgr_delay']
    dbline.det_dilation = form.cleaned_data['det_dilation']
    dbline.det_erosion = form.cleaned_data['det_erosion']
    dbline.det_max_size = form.cleaned_data['det_max_size']
    dbline.det_max_rect = form.cleaned_data['det_max_rect']
    dbline.det_scaledown = form.cleaned_data['det_scaledown']
    await dbline.asave(update_fields=[
      'det_fpslimit', 
      'det_threshold',
      'det_backgr_delay',
      'det_dilation',
      'det_erosion',
      'det_max_size',
      'det_max_rect',
      'det_scaledown',
    ])
    await asyncio.to_thread(mycam.inqueue.put, (('reset_cam',)), )
    return HttpResponseRedirect(myurl+str(detnr)+'/')

  async def check_access(self, request, detnr, tokennr, token):
    if await database_sync_to_async(lambda: request.user.is_authenticated)():
      go_on = await access.check_async('D', detnr, request.user, 'R')
      may_write = await access.check_async('D', detnr, request.user, 'W')
    else:
      go_on = (tokennr and token 
        and await database_sync_to_async(checktoken)((tokennr, token), 'CAR', camnr))
      may_write = False
    return go_on, may_write   
    
def validate_form(post_data):
  form = EventerForm(post_data)
  if form.is_valid():
      return form
  return None  

class OneEveView(View):  

  async def get(self, request, evenr, tokennr=0, token=None):
    user = await database_sync_to_async(get_user)(request)
    if not user.is_authenticated:
      return redirect('/accounts/login/?next=/')
    go_on, may_write = await self.check_access(request, evenr, tokennr, token)
    if not go_on:  
      return HttpResponse('No Access to this ressource!')
    dbline = await stream.objects.aget(id=evenr)
    myurl = '/oneitem/eventer/'
    my_school = await database_sync_to_async(lambda: dbline.eve_school)()
    form = EventerForm(initial={
      'eve_fpslimit' : dbline.eve_fpslimit,
      'eve_margin' : dbline.eve_margin,
      'eve_event_time_gap' : dbline.eve_event_time_gap,
      'eve_shrink_factor' : dbline.eve_shrink_factor,
      'eve_sync_factor' : dbline.eve_sync_factor,
      'eve_school' :  my_school,
      'eve_alarm_email' : dbline.eve_alarm_email,
    })
    context = {
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'debug' : settings.DEBUG,
      'may_write' : may_write,
      'tokennr' : tokennr,
      'token' : token,
      'user' : request.user,
      'dbline' : dbline,
      'camlist': await filter_items(stream, 'C', request.user, 'R'),
      'detectorlist': await filter_items(stream, 'D', request.user, 'R'),
      'eventerlist': await filter_items(stream, 'E', request.user, 'R'),
      'schoollist': await filter_items(school, 'S', request.user, 'R'),
      'schoollist_write': await filter_items(school, 'S', request.user, 'W'),
      'myurl' : myurl,
      'form' : form,
    }
    return render(request, 'oneitem/oneeventer.html', context) 
    
  async def post(self, request, evenr, tokennr=0, token=None):
    if not await database_sync_to_async(get_user)(request):
      return JsonResponse({"error": "unauthorized"}, status=401)
    go_on, may_write = await self.check_access(request, evenr, tokennr, token)
    if not go_on:
        return HttpResponse('No Access!')
    dbline = await stream.objects.aget(id=evenr)
    mycam = viewables[evenr]['C']
    myurl = '/oneitem/eventer/'
    form = await asyncio.to_thread(validate_form, request.POST)
    if not form:
      return HttpResponse('Invalid form data', status=400)
    dbline.eve_fpslimit = form.cleaned_data['eve_fpslimit']
    dbline.eve_margin = form.cleaned_data['eve_margin']
    dbline.eve_event_time_gap = form.cleaned_data['eve_event_time_gap']
    dbline.eve_shrink_factor = form.cleaned_data['eve_shrink_factor']
    dbline.eve_sync_factor = form.cleaned_data['eve_sync_factor']
    dbline.eve_school = form.cleaned_data['eve_school']
    dbline.eve_alarm_email = form.cleaned_data['eve_alarm_email']
    await dbline.asave(update_fields=[
      'eve_fpslimit', 
      'eve_margin',
      'eve_event_time_gap',
      'eve_shrink_factor',
      'eve_sync_factor',
      'eve_school',
      'eve_alarm_email',
    ])
    await asyncio.to_thread(mycam.inqueue.put, (('reset_cam',)), )
    return HttpResponseRedirect(myurl+str(evenr)+'/')

  async def check_access(self, request, evenr, tokennr, token):
    if await database_sync_to_async(lambda: request.user.is_authenticated)():
      go_on = await access.check_async('E', evenr, request.user, 'R')
      may_write = await access.check_async('E', evenr, request.user, 'W')
    else:
      go_on = (tokennr and token 
        and await database_sync_to_async(checktoken)((tokennr, token), 'CAR', camnr))
      may_write = False
    return go_on, may_write   

