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
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, gethostbyaddr, herror
from concurrent.futures import ThreadPoolExecutor
from requests import get as rget
from ipaddress import ip_network, ip_address
from psutil import net_if_addrs
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

def get_ip_address():
  s = socket(AF_INET, SOCK_DGRAM)
  s.settimeout(0.1)
  s.connect(('10.255.255.255', 1))
  my_ip = s.getsockname()[0]
  s.close()
  return(ip_address(my_ip))
  
def get_ip_network(my_ip):  
  do_break = False
  for interface in (mylist := net_if_addrs()):
    for connection in mylist[interface]:
      if connection.address == str(my_ip):
        subnetmask = connection.netmask
        do_break = True
        break
    if do_break:
      break  
  return(ip_network(str(my_ip)+'/'+subnetmask, strict=False))
  
def sortfunc(myinput):
  return(myinput['address']['ip'])
      
class search_executor(ThreadPoolExecutor):
  def __init__(self, net, ip, ports, url, onvif_name='', onvif_pass='', *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.net = net
    self.ip = ip
    self.ports = ports
    self.url = url
    self.onvif_name = onvif_name
    self.onvif_pass = onvif_pass
    if self.url:
      self.iplist = [url, ]
    else:  
      self.iplist = self.net.hosts()
    self.all_results = []
    for item in self.iplist:
      if item != self.ip:
        f = self.submit(self.scan_one, item)
        f.add_done_callback(self.callback)
    self.shutdown()
    self.all_results.sort(key = sortfunc)
        
      
  def scan_one(self, my_ip, oa_name='', oa_pass=''):
    my_ip = str(my_ip)
    result = {}
    socketdict = {}
    for port in self.ports:
      socketdict[port] = socket(AF_INET, SOCK_STREAM)
      socketdict[port].settimeout(0.1)
      try:
        socketdict[port].connect((my_ip, port))
        socketdict[port].close()
        if 'address' in result:
          result['address']['ports'].append(port)
        else:
          result['address'] = {}
          result['address']['ip'] = my_ip
          try:
            result['address']['name'] = gethostbyaddr(my_ip)[0]
          except herror:
            result['address']['name'] = 'name unknown'
          result['address']['ports'] = [port]
      except:
        pass
      finally:
        socketdict[port].close()
    return(result)
    
  def callback(self, f):
    if (myresult := f.result()):
      for port in myresult['address']['ports']:
        if port in {80, 8000}:
          try:
            myonvif = ONVIFCamera(
              myresult['address']['ip'], 
              port, 
              self.onvif_name, 
              self.onvif_pass, 
              wsdl_dir,
            ) 
            myresult['onvif']= {}
            myresult['onvif']['port'] = port 
            myresult['onvif']['info'] = myonvif.devicemgmt.GetDeviceInformation()
            media_service = myonvif.create_media_service()
            params = media_service.create_type('GetStreamUri')
            profiles = media_service.GetProfiles()
            myprofiles = [item['Name'] for item in profiles]
            myresult['onvif']['profiles'] = myprofiles 
            myresult['onvif']['profilenr'] = 0
            myprofile = profiles[myresult['onvif']['profilenr']]
            params['StreamSetup'] = {
              'Stream' : RTP_UNICAST,
              'Transport' : RTSP,
            }
            params['ProfileToken'] = myprofile.token
            myresult['onvif']['urlstart'] = media_service.GetStreamUri(params)['Uri']
            myresult['onvif']['urlscheme'] = myresult['onvif']['urlstart'].replace('://', '://{user}:{pass}@')
            myresult['onvif']['user'] = self.onvif_name
            myresult['onvif']['pass'] = self.onvif_pass
            break
          except:
            pass
      for port in myresult['address']['ports']:
        if port in {80, 8000}:
          url = 'http://'+myresult['address']['ip'] + ':' + str(port) + '/SDK/activateStatus'
          try:
            response = rget(url)
            if response.status_code == 200:
              lines = response.text.splitlines()
              i = 0
              while i < 3:
                if lines[i].startswith('<ActivateStatus'): 
                  if lines[i + 1].startswith('<Activated>') and  lines[i + 1].endswith('</Activated>'):
                    tempstring = lines[i + 1].replace('<Activated>', '')
                    tempstring = tempstring.replace('</Activated>', '')
                    if (tempstring == 'true') or (tempstring == 'false'):
                      myresult['isapi'] = {}
                      myresult['isapi']['port'] = port
                    if tempstring == 'true':
                      myresult['isapi']['activated'] = True
                    if tempstring == 'false':
                      myresult['isapi']['activated'] = False
                    if (tempstring == 'true') or (tempstring == 'false'):
                      break
                i += 1  
              break
          except:
            pass
      self.all_results.append(myresult)

class c_camera():
  
  def __init__(self, onvif_ip=None, onvif_port=None, admin_user=None, admin_passwd=None, 
      profilenr=0, url=None, logger=None):
    print(onvif_ip, onvif_port, admin_user, admin_passwd, profilenr, url, logger) 
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
      #except exceptions.ONVIFError:
      #  self.status = 'ONVIF: No Connection'
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
        
    
