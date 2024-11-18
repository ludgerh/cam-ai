"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

from email.mime.image import MIMEImage
from django.core.mail import send_mail, EmailMultiAlternatives
from threading import Thread
from time import sleep

def smtp_send_try_mail(*args, html_message = None, images = None, logger = None, ):
  count = 0
  done = False
  while count < 5:
    count += 1
    if images:
      email = EmailMultiAlternatives(*args)
      email.attach_alternative(html_message, "text/html")
      for item in images:
        mime_image = MIMEImage(item[2], _subtype=item[3])
        mime_image.add_header('Content-ID', 'image' + str(item[0]))
        email.attach(mime_image)
      result = email.send()
    else:
      result = send_mail(*args, 
        html_message = html_message, 
        fail_silently=True
      )
    if result:  
      done = True
      break
    else: 
      if logger is not None:
        logger.warning('*** ['+str(count)+'] Email sending to: ' + args[3][0] + ' failed')
      sleep(60)
  if done: 
    if logger is not None:
      logger.info('*** ['+str(count)+'] Sent email to: ' + args[3][0]) # args[3] is receiver
      
def smtp_send_mail(*args, **kwargs):
  Thread(target = smtp_send_try_mail, name = 'SMTPSendThread', 
    args = args, kwargs = kwargs).start()
