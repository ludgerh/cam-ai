import numpy as np
import cv2 as cv
from time import time
from logging import getLogger
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from access.c_access import access
from tools.c_redis import myredis
from tools.c_tools import c_convert
from tools.c_logger import log_ini
from streams.startup import streams

logname = 'viewersviews'
logger = getLogger(logname)
log_ini(logger, logname)

redis = myredis()

def getjpg(request, mode, idx, xdim, ydim, counter):
  if access.check(mode, idx, request.user, 'R'):
    if mode == 'C':
      myview = streams[idx].mycam.viewer
    elif mode == 'D':
      myview = streams[idx].mydetector.viewer
    elif mode == 'E':
      myview = streams[idx].mydetector.myeventer.viewer
    view_queue = myview.inqueue
    frame = view_queue.get()[1]
    if mode == 'D':
      if myview.drawpad.show_mask and (myview.drawpad.mask is not None):
        frame = cv.addWeighted(frame, 1, (255-myview.drawpad.mask), 0.3, 0)
    elif mode == 'C':
      if myview.drawpad.show_mask and (myview.drawpad.mask is not None):
        frame = cv.addWeighted(frame, 1, (255-myview.drawpad.mask), -0.3, 0)
    if mode in {'C', 'D'}:
      if myview.drawpad.edit_active and myview.drawpad.ringlist:
        if myview.drawpad.whitemarks:
          frame = cv.addWeighted(frame, 1, (255-myview.drawpad.screen), 1, 0)
        else:
          frame = cv.addWeighted(frame, 1, (255-myview.drawpad.screen), -1.0, 0)
    if (xdim > 0) or (ydim > 0):
      frame = c_convert(frame, typein=3, xout=xdim, yout=ydim)
    frame = c_convert(frame, typein=3, typeout=1)
    return HttpResponse(frame, content_type="image/jpeg")
  else:
    return(HttpResponse('No Access'))

def c_canvas(request, displaymode, mode, idx, xdim, ydim):
  if access.check(mode, idx, request.user, 'R'):
    if request.user.is_authenticated:
      name_to_use = redis.name_from_stream(idx).decode()
    else:
      name_to_use = 'This ist realtime.'
    xydims = redis.x_y_res_from_cam(idx)
    context = {
      'name' : name_to_use,
      'xres' : xydims[0],
      'yres' : xydims[1],
      'width' : xdim,
      'height' : ydim,
      'mode' : mode,
      'idx' : idx,
      'dmode' : displaymode,
    }
    template = loader.get_template('viewers/c_canvas.html')
    return(HttpResponse(template.render(context)))
  else:
    return(HttpResponse('No Access'))
