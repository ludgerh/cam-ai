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
from socket import gaierror
from pathlib import Path
from aiosmtplib import (
  SMTP,
  SMTPAuthenticationError, 
  SMTPServerDisconnected,
  SMTPRecipientsRefused,
  SMTPConnectError,
  SMTPSenderRefused,
)
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email import encoders
from .c_tools import get_smtp_conf

class l_msg(MIMEMultipart):

  def __init__(self, sender_email, receiver_email, subject, plain_body, html=None):
    super().__init__('mixed')
    self["From"] = sender_email
    self["To"] = receiver_email
    self["Subject"] = subject
    if html:
      part = MIMEMultipart("alternative")
      part.attach(MIMEText(plain_body, "plain"))
      part.attach(MIMEText(html, "html"))
    else:
      part = MIMEText(plain_body, 'plain')
    self.attach(part)
      
  def attach_file(self, file_path):
    # accept both str and Path
    file_path = Path(file_path)      # normalize to Path
    with open(file_path, "rb") as f:
      part = MIMEBase("application", "octet-stream")
      part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
      "Content-Disposition",
      f"attachment; filename={file_path.name}"  # use only filename
    )
    self.attach(part)
    
  def attach_jpeg(self, jpeg_data, c_id = None):  
    mime_image = MIMEImage(jpeg_data, _subtype='jpeg')
    if c_id:
      mime_image.add_header('Content-ID', c_id)
    self.attach(mime_image)
    
  def get_size(self):
    return len(self.as_string())    

class l_smtp(SMTP):

  def __init__(self, **kwargs):
    if kwargs['host'] == '':
      self.answer = 'There is no valid SMTP configuration.'
      self.last_error = (6, 'No SMTP config')
      self.result_code = 6
      self.ready = False
      return(None)
    else:
      self.ready = True  
    self.allowed_size = None
    self.answer = 'OK'
    self.last_error = (0, 'OK')
    self.result_code = 0
    if 'timeout' not in kwargs:
      kwargs['timeout'] = 5.0
    if 'user' in kwargs:
      self.user = kwargs['user']
    else:
      self.user = ''  
    if 'password' in kwargs:
      self.password = kwargs['password']
    else:
      self.password = ''  
    super().__init__(
      hostname = kwargs['host'],
      port = kwargs['port'],
      timeout = kwargs['timeout'],
      start_tls=False,
    )
    self._kwargs = kwargs
    
  async def async_init(self):
    if not self.ready:
      return(None)
    kwargs = self._kwargs  
    try: 
      await self.connect()
      code, response = await self.ehlo()
      self.connect_code = code
      if isinstance(response, bytes):
        response_lines = response.decode().splitlines()
      else:
        response_lines = str(response).splitlines()
      self.greeting = response_lines[0]  
      self.esmtp_features = {}
      for line in response_lines[1:]:
        parts = line.strip().split()
        if parts:
          key = parts[0].upper()
          val = " ".join(parts[1:]) if len(parts) > 1 else ""
          self.esmtp_features[key] = val
      if 'STARTTLS' in self.esmtp_features:
        await self.starttls()
      if 'user' in kwargs: 
        if 'password' in kwargs: 
          await self.login(kwargs['user'], kwargs['password']) 
        else:  
          await self.login(kwargs['user'], '') 
      self.allowed_size = int(self.esmtp_features['SIZE'])
    except gaierror as e:
      self.answer = 'Domain is not reachable. Spelling?'
      self.last_error = e.args
      self.result_code = 1
    except TimeoutError as e:
      self.answer = 'Timeout. Wrong server? Wrong port?'
      self.last_error = e.args
      self.result_code = 2
    except ConnectionRefusedError as e:
      self.answer = 'Server refused connection. Wrong server? Wrong port?'
      self.last_error = e.args
      self.result_code = 3
    except SMTPAuthenticationError as e:
      self.answer = 'Authentication error. Wrong username? Wrong password?'
      self.last_error = e.args
      self.result_code = 4
    except SMTPConnectError as e:
      self.answer = 'Server refused to connect your IP.'
      self.last_error = e.args
      self.result_code = 5
    except Exception as e:
      self.answer = 'Something else went wrong: ' + str(e.args) 
      self.last_error = e.args
      self.result_code = 1001
      
  async def sendmail(self, *args):
    if not self.ready:
      return(None)
    msg = args[2]
    if self.allowed_size and msg.get_size() > self.allowed_size:
      self.answer = 'This Email is too large for the SMTP-Server.'
      self.last_error = (10001, 'Email too large')
      self.result_code = 10001
      return({'Server-Error' : 'Email too large', })
    self.answer = 'OK'
    self.last_error = (0, 'OK')
    try:
      return await super().sendmail(*args[:2], msg.as_string()) 
      self.result_code = 0
    except SMTPRecipientsRefused as e:
      self.answer = 'Server refused to take the mail. Wrong username? Wrong password? Wrong testing email?'
      self.last_error = e.args
      self.result_code = 10002
    except SMTPSenderRefused as e:
      self.answer = 'Server refused to take the mail. Wrong username? Wrong password? Wrong sending email?'
      self.last_error = e.args
      self.result_code = 10003
    except Exception as e:
      self.answer = 'Something else went wrong: ' + str(e.args) 
      self.last_error = e.args 
      self.result_code = 11001
      return({'Server-Error' : 'Other error', })
 
  async def is_connected(self):
    if not self.ready:
      return(None)
    try:
      await self.noop()
      return(True)
    except SMTPServerDisconnected:
      return(False)
      
  async def quit(self):
    if not self.ready:
      return(None)
    if await self.is_connected():
      await super().quit()

def async_sendmail(receiver_email, subject, message, html = None):
  smtp_conf = get_smtp_conf()
  my_smtp = l_smtp(**smtp_conf)
  loop = asyncio.new_event_loop()
  asyncio.set_event_loop(loop)
  loop.run_until_complete(my_smtp.async_init())
  my_msg = l_msg(
    smtp_conf['sender_email'],
    receiver_email,
    subject,
    message,
    html,
  )
  loop.run_until_complete(my_smtp.sendmail(
    smtp_conf['sender_email'],
    receiver_email,
    my_msg,
  ))
  loop.run_until_complete(my_smtp.quit())
  loop.close()
      
