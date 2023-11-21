# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
# More information and komplete source: https://github.com/ludgerh/cam-ai
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

from shutil import disk_usage
from multitimer import MultiTimer
from os import path, remove
from logging import getLogger
from eventers.models import event, event_frame
from .c_logger import log_ini
from .l_tools import djconf

logname = 'health'
logger = getLogger(logname)
log_ini(logger, logname)
datapath = djconf.getconfig('datapath', 'data/')
schoolframespath = djconf.getconfig('schoolframespath', datapath + 'schoolframes/')
recordingspath = djconf.getconfig('recordingspath', datapath + 'recordings/')

totaldiscspace = 1
freediscspace = 1

def setdiscspace():
  global totaldiscspace
  global freediscspace
  total, used, free = disk_usage("/")
  totaldiscspace = total
  freediscspace = free

setdiscspace()

def healthcheck():
  setdiscspace()
  if (delthresh := djconf.getconfigfloat('deletethreshold', 0.0)):
    if (freediscspace / totaldiscspace * 100.0) < delthresh:
      setdiscspace()
      eventline = event.objects.filter(xmax__gt=0).first()
      if eventline:
        logger.warning('Health Check purged event #'+str(eventline.id)+'. Free disk space:'+str(freediscspace))
        framelines = event_frame.objects.filter(event__id=eventline.id)
        for item in framelines:
          framefile = schoolframespath + item.name
          if path.exists(framefile):
            remove(framefile)
          else:
            logger.warning('Health Check - Delete did not find: ' + framefile)
        framelines.delete()
        if eventline.videoclip:
          if event.objects.filter(videoclip=eventline.videoclip).count() <= 1:
            videofile = recordingspath + eventline.videoclip
            if path.exists(videofile + '.mp4'):
              remove(videofile + '.mp4')
            else:
              logger.warning('Health Check - Delete did not find: ' + videofile + '.mp4')
            if path.exists(videofile + '.webm'):
              remove(videofile + '.webm')
            else:
              logger.warning('Health Check - Delete did not find: ' + videofile + '.webm')
            if path.exists(videofile + '.jpg'):
              remove(videofile + '.jpg')
            else:
              logger.warning('Health Check - Delete did not find: ' + videofile + '.jpg')
        eventline.delete()

mytimer = MultiTimer(interval=10, function=healthcheck, runonstart=False)
mytimer.start()

def stop():
  mytimer.stop()


  
