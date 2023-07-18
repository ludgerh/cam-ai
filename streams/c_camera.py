# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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

import json
from onvif import ONVIFCamera, exceptions, init_log
from subprocess import Popen, PIPE

# Constants:
# stream type
RTP_UNICAST = 0
RTP_MULTICAST = 1
# transport protocol
UDP = 0
TCP = 1
RTSP = 2
HTTP = 3
# userlevel
ADMINISTRATOR = 0
OPERATOR = 1
USER = 2
ANONYMOUS = 3
EXTENDED = 4

wsdl_dir = 'onvif/wsdl/'

def logger_init(logger):
  init_log(logger)

class c_camera():
  
  def __init__(self, onvif_ip=None, onvif_port=None, admin_user=None, admin_passwd=None, 
      profilenr=0, url=None, logger=None):
    self.status = 'OK'
    self.online = False
    self.onvif_ip = onvif_ip
    self.onvif_port = onvif_port
    self.admin_user = admin_user
    self.admin_passwd = admin_passwd
    self.url = url
    if self.onvif_ip and self.onvif_port:
      try:
        self.myonvif = ONVIFCamera(
          self.onvif_ip, 
          self.onvif_port, 
          self.admin_user, 
          self.admin_passwd, 
          wsdl_dir,
        )
        self.deviceinfo = self.myonvif.devicemgmt.GetDeviceInformation()
        media_service = self.myonvif.create_media_service()
        params = media_service.create_type('GetStreamUri')
        profiles = media_service.GetProfiles()
        self.onvif_profile = profiles[profilenr]
        params['StreamSetup'] = {
          'Stream' : RTP_UNICAST,
          'Transport' : RTSP,
        }
        params['ProfileToken'] = self.onvif_profile.token
        urlstart = media_service.GetStreamUri(params)['Uri']
      except exceptions.ONVIFError:
        self.status = 'ONVIF: No Connection'
      except IndexError:
        self.status = 'ONVIF: Profile ' + str(profilenr) + ' does not exist'
      if self.status == 'OK':
        self.urlscheme = urlstart.replace('://', '://{user}:{pass}@')
        self.adminurl = urlstart.replace('://', '://' + self.admin_user + ':'
          + self.admin_passwd+'@')
          
  def create_users(self, name, passwd, level=USER):
    params = self.myonvif.devicemgmt.create_type('CreateUsers')
    params['User'].append({'Username' : name, 'Password' : passwd, 'UserLevel' : level, })
    return(self.myonvif.devicemgmt.CreateUsers(params))
    
  def set_users(self, name, passwd, level=USER):
    params = self.myonvif.devicemgmt.create_type('SetUser')
    params['User'].append({'Username' : name, 'Password' : passwd, 'UserLevel' : level, })
    return(self.myonvif.devicemgmt.SetUser(params))
    
  def get_userlist(self): 
    return(self.myonvif.devicemgmt.GetUsers())
    
  def get_user(self, name):
    userlist = self.get_userlist()
    for item in userlist:
      if (item['Username'] == name):
        return(item)
    return(None)
      
  def ffprobe(self):
    if not self.url:
      self.url = self.adminurl
    cmds = ['ffprobe', '-v', 'fatal', '-print_format', 'json', 
      '-show_streams', self.url]
    p = Popen(cmds, stdout=PIPE)
    output, _ = p.communicate()
    self.probe = json.loads(output)
    if len(self.probe) > 0:
      self.online = True
    else:
      self.status = 'FFPROBE: No result'
        
    
