# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
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

from smtplib import SMTP, SMTP_SSL
from ssl import create_default_context
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class l_smtp():

  def __init__(self, mode, server, port=None):
    context = create_default_context()
    if mode == 'SSL':
      if port is None:
        port = 465
      self.connection = SMTP_SSL(
        host=server, 
        port=port, 
        context=context,
      )   
    elif mode == 'STARTTLS':
      if port is None:
        port = 587
      self.connection = SMTP(
        host=server, 
        port=port, 
      )
      self.connection.ehlo()
      self.connection.starttls()
    #self.connection.set_debuglevel(2)
    
  def login(self, user, password):
    self.connection.login(user, password)
    
  def putcontent(self, subject, from_name, from_email, to_email, plain_text, html_text):
    self.msg = MIMEMultipart('alternative')
    self.msg['Subject'] = subject
    self.msg['From'] = from_name + '<' + from_email + '>'
    self.msg['To'] = to_email
    self.msg.attach(MIMEText(plain_text, 'plain'))
    self.msg.attach(MIMEText(html_text, 'html'))
    self.msg = self.msg.as_string()
    
  def sendmail(self, from_addr, to_addrs):
    self.connection.sendmail(from_addr, to_addrs, self.msg)
    
  def logout(self):
    self.connection.quit()
