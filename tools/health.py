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

import aiofiles
import aiofiles.os
from asgiref.sync import sync_to_async
from shutil import disk_usage
from logging import getLogger
from eventers.models import event, event_frame
from users.models import userinfo
from .c_logger import alog_ini
from .l_tools import djconf
from .l_break import a_break_time
from .l_smtp import l_smtp, l_msg
from .c_tools import get_smtp_conf
from .redis import my_redis as tools_redis

class health_runner():
  def __init__(self):
    self.do_run = True
    self.totaldiscspace = 1
    self.freediscspace = 1
    self.useddiscspace = 1
    datapath = djconf.getconfig('datapath', 'data/')
    self.schoolframespath = djconf.getconfig(
      'schoolframespath', 
      datapath + 'schoolframes/',
    )
    self.recordingspath = djconf.getconfig(
      'recordingspath', 
      datapath + 'recordings/',
    )
    
  def get_totaldiscspace(self):
    return(tools_redis.get_totaldiscspace())
    
  def set_totaldiscspace(self, value):
    tools_redis.set_totaldiscspace(value) 
    
  totaldiscspace = property(get_totaldiscspace, set_totaldiscspace)    
    
  def get_freediscspace(self):
    return(tools_redis.get_freediscspace())
    
  def set_freediscspace(self, value):
    tools_redis.set_freediscspace(value) 
    
  freediscspace = property(get_freediscspace, set_freediscspace)      
    
  def get_useddiscspace(self):
    return(tools_redis.get_useddiscspace())
    
  def set_useddiscspace(self, value):
    tools_redis.set_useddiscspace(value)  
    
  useddiscspace = property(get_useddiscspace, set_useddiscspace)    
    
  async def setdiscspace(self):  
    self.totaldiscspace, self.useddiscspace, self.freediscspace = disk_usage("/")
    userlines = userinfo.objects.filter(user__is_superuser = True)
    if self.useddiscspace > self.totaldiscspace * 0.95:
      userlines = await sync_to_async(list)(
          userinfo.objects.filter(mail_flag_discspace95=True)
      )
      for userline in userlines:
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
          await userline.save(update_fields = ['mail_flag_discspace95', ]) 
    else:  
      userlines = await sync_to_async(list)(
          userinfo.objects.filter(mail_flag_discspace95=True)
      )
      for userline in userlines:
        if userline.mail_flag_discspace95:
          userline.mail_flag_discspace95 = False 
          userline.save(update_fields = ['mail_flag_discspace95', ]) 

  async def health_task(self):
    logname = 'health'
    self.logger = getLogger(logname)
    await alog_ini(self.logger, logname)
    while self.do_run:
      #print('**** Health Task *****')
      await self.setdiscspace()
      if (delthresh := (await djconf.agetconfigfloat('deletethreshold', 0.0))):
        if (self.freediscspace / self.totaldiscspace * 100.0) < delthresh:
          eventline = await event.objects.filter(xmax__gt=0).afirst()
          if eventline:
            self.logger.warning('Health Check purged event #'
              + str(eventline.id)+'. Free disk space:'+str(self.freediscspace))
            framelines = await event_frame.objects.filter(event__id=eventline.id).aall()
            for item in framelines:
              framefile = schoolframespath + item.name
              if await aiofiles.os.path.exists(framefile):
                await aiofiles.os.remove(framefile)
              else:
                self.logger.warning('Health Check - Delete did not find: ' + framefile)
            await framelines.adelete()
            if eventline.videoclip:
              if event.objects.filter(videoclip=eventline.videoclip).count() <= 1:
                videofile = recordingspath + eventline.videoclip
                if await aiofiles.os.path.exists(videofile + '.mp4'):
                  await aiofiles.os.remove(videofile + '.mp4')
                else:
                  self.logger.warning('Health Check - Delete did not find: ' 
                    + videofile + '.mp4')
                if await aiofiles.os.path.exists(videofile + '.webm'):
                  await aiofiles.os.remove(videofile + '.webm')
                else:
                  self.logger.warning('Health Check - Delete did not find: ' 
                    + videofile + '.webm')
                if await aiofiles.os.path.exists(videofile + '.jpg'):
                  await aiofiles.os.remove(videofile + '.jpg')
                else:
                  self.logger.warning('Health Check - Delete did not find: ' 
                    + videofile + '.jpg')
            await eventline.adelete()
      await a_break_time(60.0)   

  def stop(self):
    self.do_run = False
    
my_health_runner = health_runner()  


  
