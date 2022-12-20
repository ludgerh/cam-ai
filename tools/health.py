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
schoolframespath = djconf.getconfig('schoolframespath', 'data/schoolframes/')
recordingspath = djconf.getconfig('recordingspath', 'data/recordings/')

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


  
