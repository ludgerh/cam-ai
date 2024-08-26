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

from django.core.mail import send_mail
from threading import Thread
from time import sleep

def smtp_send_try_mail(subject, plain_text, sender, receiver, html_text, logger):
  count = 0
  while count < 5:
    count += 1
    if send_mail(
      subject,
      plain_text,
      sender,
      [receiver],
      fail_silently=True,
      html_message=html_text,
    ):
      break
    else: 
      logger.warning('*** ['+str(count)+'] Email sending to: '+receiver+' failed')
      sleep(300)
  logger.info('*** ['+str(count)+'] Sent email to: '+receiver)
      
def smtp_send_mail(subject, plain_text, sender, receiver, html_text, logger):
  Thread(target=smtp_send_try_mail, name='SMTPSendThread', 
    args=(subject, plain_text, sender, receiver, html_text, logger)
    ).start()
