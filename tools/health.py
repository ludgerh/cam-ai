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

from shutil import disk_usage
from multitimer import MultiTimer
from os import path, remove
from logging import getLogger
from eventers.models import event, event_frame
from users.models import userinfo
from .c_logger import log_ini
from .l_tools import djconf
from .l_smtp import l_smtp, l_msg
from .c_tools import list_from_queryset, get_smtp_conf

logname = 'health'
logger = getLogger(logname)
log_ini(logger, logname)
datapath = djconf.getconfig('datapath', 'data/')
schoolframespath = djconf.getconfig('schoolframespath', datapath + 'schoolframes/')
recordingspath = djconf.getconfig('recordingspath', datapath + 'recordings/')

totaldiscspace = 1
freediscspace = 1
useddiscspace = 1

def setdiscspace():
  global totaldiscspace
  global freediscspace
  global useddiscspace
  totaldiscspace, useddiscspace, freediscspace = disk_usage("/")
  if useddiscspace > totaldiscspace * 0.95:
    for userline in list_from_queryset(
        userinfo.objects.filter(user__is_superuser = True)
      ):
      if not userline.mail_flag_discspace95:
        print('Server Capacity 95')
        
        
        smtp_conf = get_smtp_conf()
        my_smtp = l_smtp(**smtp_conf)
        my_msg = l_msg(
          smtp_conf['sender_email'],
          userline.user.email,
          'Important: Your CAM-AI Server Storage is Nearly Full',
          ('Dear CAM-AI Server Administrator, \n'
            + 'We would like to inform you that your server’s storage capacity has reached 95%. \n'
            + 'To prevent any potential disruptions to your CAM-AI services, we recommend reviewing and managing your storage usage. \n'
            + 'You may either delete unnecessary data or increase your server’s capacity as needed. \n'
            + 'If you have any questions or need assistance, please don’t hesitate to contact us at info@cam-ai.de \n'
            + 'Thank you for choosing CAM-AI. \n'
            + 'Best regards, \n'
            + 'The CAM-AI Team'),
          html = ('<br>Dear CAM-AI Server Administrator,<br>\n'
            + '<br>We would like to inform you that your server’s storage capacity has reached 95%.\n'
            + 'To prevent any potential disruptions to your CAM-AI services, we recommend reviewing and managing your storage usage. \n'
            + 'You may either delete unnecessary data or increase your server’s capacity as needed. <br>\n'
            + '<br>If you have any questions or need assistance, please don’t hesitate to contact us at info@cam-ai.de <br>\n'
            + '<br>Thank you for choosing CAM-AI.<br>\n'
            + '<br>Best regards,<br>\n'
            + 'The CAM-AI Team<br>\n'
            + '<br><br><p style="color: lightgrey;">This email was sent automatically by the CAM-AI system.</p>'
          )
        )
        my_smtp.sendmail(
          smtp_conf['sender_email'],
          userline.user.email,
          my_msg,
        )
        if my_smtp.result_code:
          self.logger.error('SMTP: ' + my_smtp.answer)
          self.logger.error(str(my_smtp.last_error))
        my_smtp.quit()
        userline.mail_flag_discspace95 = True 
        userline.save(update_fields = ['mail_flag_discspace95', ]) 
  else:  
    for userline in list_from_queryset(
        userinfo.objects.filter(user__is_superuser = True)
      ):  
      if userline.mail_flag_discspace95:
        userline.mail_flag_discspace95 = False 
        userline.save(update_fields = ['mail_flag_discspace95', ]) 

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


  
