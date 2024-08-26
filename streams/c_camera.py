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

import json
import xml.etree.ElementTree as ET
from socket import (socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, gethostbyaddr, herror, 
  timeout, gaierror)
from concurrent.futures import ThreadPoolExecutor
from requests import get as rget, put as rput
from requests.auth import HTTPDigestAuth
from ipaddress import ip_network, ip_address
from urllib.parse import urlparse
from psutil import net_if_addrs
from onvif import ONVIFCamera, exceptions, init_log
from subprocess import Popen, PIPE
from tools.c_redis import myredis

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

def logger_init(logger):
  init_log(logger)
  
def sortfunc(myinput):
  return(ip_address(myinput['address']['ip']))
      
class search_executor(ThreadPoolExecutor):
  def __init__(self, net, ip, ports, url, uname='', upass='', *args, **kwargs):
    self.thread_count = 0
    super().__init__(*args, **kwargs)
    self.net = net
    self.ip = ip
    self.ports = ports
    self.url = url
    self.uname = uname
    self.upass = upass
    if self.url:
      self.iplist = [url, ]
    else:  
      self.iplist = self.net.hosts()
    self.all_results = []
    for item in self.iplist:
      if str(item) != self.ip:
        f = self.submit(self.scan_one, item)
        f.add_done_callback(self.callback)
    
  def stop(self):
    self.shutdown()
    if len(self.all_results) > 1: #Domain String entered
      self.all_results.sort(key = sortfunc)
        
      
  def scan_one(self, my_ip):
    self.thread_count += 1
    my_ip = str(my_ip)
    result = {}
    socketdict = {}
    for port in self.ports:
      socketdict[port] = socket(AF_INET, SOCK_STREAM)
      socketdict[port].settimeout(1.0)
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
      except gaierror:
        result['error'] = 'domain_error'
      except timeout:
        result['error'] = 'ip_error'
      except OSError:
        result['error'] = 'ip_error'
      finally:
        socketdict[port].close()
    return(result)
    
  def callback(self, f):
    myresult = f.result()
    if myresult and 'address' in myresult:
      for port in myresult['address']['ports']:
        if port in {80, 2020, 8000, 8080}:
          try:
            myonvif = ONVIFCamera(
              myresult['address']['ip'], 
              port, 
              self.uname, 
              self.upass, 
              wsdl_dir,
              force_host = True,
            ) 
            myresult['onvif']= {}
            myresult['onvif']['port'] = port 
            myresult['onvif']['info'] = {}
            myinfo = myonvif.devicemgmt.GetDeviceInformation()
            for item in myinfo:
              myresult['onvif']['info'][item] = myinfo[item]
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
            scheme = myresult['onvif']['urlstart'].split("//")[0]
            right = myresult['onvif']['urlstart'].split("//")[1]
            address = right.split("/")[0]
            ip_address = address.split(":")[0]
            port_address = address.split(":")[1]
            remaining = '/'.join(right.split('/')[1:])
            myresult['onvif']['urlstart'] = (scheme + '//{address}:' 
              + port_address + '/' + remaining)
            myresult['onvif']['stream_port'] = port_address
            myresult['onvif']['urlscheme'] = myresult['onvif']['urlstart'].replace('://', '://{user}:{pass}@')
            myresult['onvif']['user'] = self.uname
            myresult['onvif']['pass'] = self.upass
            break
          except:
            pass 
               
      for port in myresult['address']['ports']:
        if port in {80, 8000}:
          url = 'http://'+myresult['address']['ip'] + ':' + str(port) + '/SDK/activateStatus'
          try:
            response = rget(url)
            if response.status_code == 200:
              tempstring = ''
              root = ET.fromstring(response.text)
              ns = root.tag.find('}') + 1
              namespace = root.tag[:ns]
              if root.tag[ns:] == 'ActivateStatus':
                child = root.find(namespace + 'Activated')
                tempstring = child.text
                if (tempstring == 'true') or (tempstring == 'false'):
                  myresult['isapi'] = {}
                  myresult['isapi']['port'] = port
                if tempstring == 'true':
                  myresult['isapi']['activated'] = True
                if tempstring == 'false':
                  myresult['isapi']['activated'] = False
                if (tempstring == 'true') or (tempstring == 'false'):
                  myresult['isapi']['user'] = self.uname
                  myresult['isapi']['pass'] = self.upass
                  myresult['isapi']['urlstart'] = 'rtsp://{address}:554/ISAPI/streaming/channels/101'
                  netloc = urlparse(myresult['isapi']['urlstart']).netloc
                  myresult['isapi']['stream_port'] = netloc.split(':')[1]
                  myresult['isapi']['urlscheme'] = myresult['isapi']['urlstart'].replace('://', '://{user}:{pass}@')
                  username = self.uname
                  password = self.upass
                  auth = HTTPDigestAuth(self.uname, self.upass)
                  url = 'http://'+myresult['address']['ip'] + ':' + str(port) + '/ISAPI/System/deviceInfo'
                  response = rget(url, auth=auth)
                  if response.status_code == 200:
                    myresult['isapi']['info'] = {}
                    root = ET.fromstring(response.text)
                    ns = root.tag.find('}') + 1
                    for child in root:
                      myresult['isapi']['info'][child.tag[ns:]] = child.text
                  url = 'http://'+myresult['address']['ip'] + ':' + str(port) + '/ISAPI/PTZCtrl/channels/1/capabilities'
                  response = rget(url, auth=auth)
                  if response.status_code == 200:
                    root = ET.fromstring(response.text)
                    ns = root.tag.find('}') + 1
                    namespace = root.tag[:ns]
                    child = root.find(namespace + 'AbsolutePanTiltPositionSpace')
                    gchild = child.find(namespace + 'XRange')
                    ggchild = gchild.find(namespace + 'Min')
                    myresult['isapi']['ptz'] = {}
                    myresult['isapi']['ptz']['pan'] = {}
                    myresult['isapi']['ptz']['pan']['min'] = int(ggchild.text)
                    ggchild = gchild.find(namespace + 'Max')
                    myresult['isapi']['ptz']['pan']['max'] = int(ggchild.text) 
                    gchild = child.find(namespace + 'YRange')
                    ggchild = gchild.find(namespace + 'Min')
                    myresult['isapi']['ptz']['tilt'] = {}
                    myresult['isapi']['ptz']['tilt']['min'] = int(ggchild.text)
                    ggchild = gchild.find(namespace + 'Max')
                    myresult['isapi']['ptz']['tilt']['max'] = int(ggchild.text)
                    child = root.find(namespace + 'AbsoluteZoomPositionSpace')
                    gchild = child.find(namespace + 'ZRange')
                    ggchild = gchild.find(namespace + 'Min')
                    myresult['isapi']['ptz']['zoom'] = {}
                    myresult['isapi']['ptz']['zoom']['min'] = int(ggchild.text)
                    ggchild = gchild.find(namespace + 'Max')
                    myresult['isapi']['ptz']['zoom']['max'] = int(ggchild.text)
                  break
              break
          except:
            pass           
    if self.url or (myresult and 'address' in myresult):
      self.all_results.append(myresult)
    self.thread_count -= 1
      
class ptz_base():
  
  def __init__(self, idx, redis, control_ip, control_port, control_user, control_pass, limits):
    self.id = idx
    self.redis = redis
    self.channel = 1 
    self.limits = limits
    self.url1 = 'http://'+ control_ip + ':' + str(control_port) + '/'
    self.headers = {'Content-Type': 'application/json'}
    self.auth = HTTPDigestAuth(control_user, control_pass)
    
    self.commandlib = {} # 0 : URL, 1 : XML
    self.commandlib['goto_abs'] = ['/ISAPI/PTZCtrl/channels/' + str(self.channel) + '/absolute', ]
    self.commandlib['goto_abs'].append("""\
<PTZData>
  <AbsoluteHigh>
    <elevation>{ypos}</elevation>
    <azimuth>{xpos}</azimuth>
    <absoluteZoom>{zoom}</absoluteZoom>
  </AbsoluteHigh>
</PTZData> """)
    self.commandlib['get_abs'] = ['/ISAPI/PTZCtrl/channels/' + str(self.channel) + '/status']
    self.commandlib['parking'] = ['/ISAPI/PTZCtrl/channels/' + str(self.channel) + '/parkaction']
    self.commandlib['parking'].append("""\
<ParkAction>
  <enabled>{enabled}</enabled>
  <Parktime>{time}</Parktime>
  <Action>
    <ActionType>{atype}</ActionType>
    <ActionNum>{anum}</ActionNum>
  </Action>
</ParkAction> """)
    self.abs_pos = self.get_abs()
    self.set_parking(False)

  def get_parking(self):
    url = self.url1 + self.commandlib['parking'][0]
    response = rget(url, headers=self.headers, auth=self.auth)
    if response.status_code == 200:
      root = ET.fromstring(response.text)
      ns = root.tag.find('}') + 1
      namespace = root.tag[:ns]
      child = root.find(namespace + 'enabled')
      enabled = (child.text == 'true')
      child = root.find(namespace + 'Parktime')
      time = int(child.text)
      child = root.find(namespace + 'Action')
      gchild = child.find(namespace + 'ActionType')
      atype = gchild.text
      gchild = child.find(namespace + 'ActionNum')
      anum = int(gchild.text)
      return((enabled, time, atype, anum))
    else:
      return(None)
      
  def set_parking(self, enabled, time=5, atype='preset', anum=32):
    url = self.url1 + self.commandlib['parking'][0]
    xml = self.commandlib['parking'][1]
    xml = xml.replace('{enabled}', str(enabled).lower(), 1)
    xml = xml.replace('{time}', str(time), 1)
    xml = xml.replace('{atype}', atype, 1)
    xml = xml.replace('{anum}', str(anum), 1)
    response = rput(url, headers=self.headers, auth=self.auth, data= xml.encode('utf-8'))
    if response.status_code == 200:
      return('OK')
    else:
      return(None)

  def get_abs(self):
    url = self.url1 + self.commandlib['get_abs'][0]
    response = rget(url, headers=self.headers, auth=self.auth)
    if response.status_code == 200:
      root = ET.fromstring(response.text)
      ns = root.tag.find('}') + 1
      namespace = root.tag[:ns]
      child = root.find(namespace + 'AbsoluteHigh')
      gchild = child.find(namespace + 'elevation')
      y = int(gchild.text)
      gchild = child.find(namespace + 'azimuth')
      x = int(gchild.text)
      gchild = child.find(namespace + 'absoluteZoom')
      z = int(gchild.text)
      return((x, y, z))
    else:
      return(None)
      
  def goto_abs(self, x=None, y=None, z=None):
    if x is None:
      x = self.abs_pos[0]
    else:  
      x = max(x, self.limits[0][0])
      x = min(x, self.limits[0][1])
    if y is None:  
      y = self.abs_pos[1]
    else:  
      y = max(y, self.limits[1][0])
      y = min(y, self.limits[1][1])
    if z is None:  
      z = self.abs_pos[2]
    else:  
      z = max(z, self.limits[2][0])
      z = min(z, self.limits[2][1])
    if ((x == self.abs_pos[0]) and (y == self.abs_pos[1]) and (z == self.abs_pos[2])):
      return(False)
    url = self.url1 + self.commandlib['goto_abs'][0]
    xml = self.commandlib['goto_abs'][1]
    xml = xml.replace('{xpos}', str(x), 1)
    xml = xml.replace('{ypos}', str(y), 1)
    xml = xml.replace('{zoom}', str(z), 1)
    response = rput(url, headers=self.headers, auth=self.auth, data= xml.encode('utf-8'))
    if response.status_code == 200:
      self.abs_pos =(x, y, z)
      self.redis.set_ptz_pos(self.id, self.abs_pos)
      return(True)
    else:
      return(None)
      
  def goto_rel(self, xin=0, yin=0, zin=0):
    if self.limits[0][2]: #goround
      x = self.abs_pos[0] + xin
      if x < 0:
        x += self.limits[0][2]
      else:  
        if x > self.limits[0][2]:
          x -= self.limits[0][2]
    else:
      x = max(self.abs_pos[0] + xin, self.limits[0][0])
      x = min(x, self.limits[0][1])
    y = max(self.abs_pos[1] + yin, self.limits[1][0])
    y = min(y, self.limits[1][1])
    z = max(self.abs_pos[2] + zin, self.limits[2][0])
    z = min(z, self.limits[2][1])
    if ((x == self.abs_pos[0]) and (y == self.abs_pos[1]) and (z == self.abs_pos[2])):
      return(False)
    url = self.url1 + self.commandlib['goto_abs'][0]
    xml = self.commandlib['goto_abs'][1]
    xml = xml.replace('{xpos}', str(x), 1)
    xml = xml.replace('{ypos}', str(y), 1)
    xml = xml.replace('{zoom}', str(z), 1)
    response = rput(url, headers=self.headers, auth=self.auth, data= xml.encode('utf-8'))
    if response.status_code == 200:
      self.abs_pos =(x, y, z)
      self.redis.set_ptz_pos(self.id, self.abs_pos)
      return(True)
    else:
      return(None)
  
class ptz_isapi(ptz_base):
  pass   
  
class ptz_onvif(ptz_base):
  pass        

class c_camera():
  
  def __init__(self, idx, control_mode=0, control_ip=None, control_port=None, control_user=None, control_pass=None, 
      profilenr=0, url=None, logger=None):
    self.id = idx  
    self.status = 'OK'
    self.online = False
    self.control_ip = control_ip
    self.control_port = control_port
    self.control_user = control_user
    self.control_pass = control_pass
    self.url = url
    self.redis = myredis()
    self.ptz = {}
    if control_mode == 0:
      self.myptz = {}
    if control_mode == 1:
      url = 'http://' + self.control_ip + ':' + str(self.control_port) + '/ISAPI/System/deviceInfo'
      auth = HTTPDigestAuth(self.control_user, self.control_pass)
      response = rget(url, auth=auth)
      self.deviceinfo = {}
      if response.status_code == 200:
        root = ET.fromstring(response.text)
        ns = root.tag.find('}') + 1
        for child in root:
          self.deviceinfo[child.tag[ns:]] = child.text
      url = 'http://' + self.control_ip + ':' + str(self.control_port) + '/ISAPI/PTZCtrl/channels/1/capabilities'
      response = rget(url, auth=auth)
      if response.status_code == 200:
        root = ET.fromstring(response.text)
        ns = root.tag.find('}') + 1
        namespace = root.tag[:ns]
        child = root.find(namespace + 'AbsolutePanTiltPositionSpace')
        gchild = child.find(namespace + 'XRange')
        ggchild = gchild.find(namespace + 'Min')
        self.ptz['pan'] = {}
        self.ptz['pan']['min'] = int(ggchild.text)
        ggchild = gchild.find(namespace + 'Max')
        self.ptz['pan']['max'] = int(ggchild.text)
        if ((self.ptz['pan']['min'] == 0) 
            and (self.ptz['pan']['max'] == 3600)):
          self.ptz['pan']['goround'] = 3600
        else:
          self.ptz['pan']['goround'] = 0
        gchild = child.find(namespace + 'YRange')
        ggchild = gchild.find(namespace + 'Min')
        self.ptz['tilt'] = {}
        self.ptz['tilt']['min'] = int(ggchild.text)
        ggchild = gchild.find(namespace + 'Max')
        self.ptz['tilt']['max'] = int(ggchild.text)
        child = root.find(namespace + 'AbsoluteZoomPositionSpace')
        gchild = child.find(namespace + 'ZRange')
        ggchild = gchild.find(namespace + 'Min')
        self.ptz['zoom'] = {}
        self.ptz['zoom']['min'] = int(ggchild.text)
        ggchild = gchild.find(namespace + 'Max')
        self.ptz['zoom']['max'] = int(ggchild.text) 
        self.myptz = ptz_isapi(
          self.id,
          self.redis,
          self.control_ip, 
          self.control_port, 
          self.control_user, 
          self.control_pass, 
          ((self.ptz['pan']['min'], self.ptz['pan']['max'], self.ptz['pan']['goround']), 
          (self.ptz['tilt']['min'], self.ptz['tilt']['max']), 
          (self.ptz['zoom']['min'], self.ptz['zoom']['max'])
        ))
        self.ptz['pos'] = self.myptz.abs_pos
    elif control_mode == 2:
      try:
        self.myonvif = ONVIFCamera(
          self.control_ip, 
          self.control_port, 
          self.control_user, 
          self.control_pass, 
          wsdl_dir,
          force_host = True,
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
        self.adminurl = urlstart.replace('://', '://' + self.control_user + ':'
          + self.control_pass+'@')
    self.redis.set_ptz(self.id, self.ptz)
          
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
    cmds = ['ffprobe', '-v', 'fatal']
    if self.url[:4].upper() == 'RTSP':
      cmds += ['-rtsp_transport',  'tcp']
    cmds += ['-print_format', 'json', '-show_streams', self.url]
    p = Popen(cmds, stdout=PIPE)
    output, _ = p.communicate()
    self.probe = json.loads(output)
    if len(self.probe) > 0:
      self.online = True
    else:
      self.status = 'FFPROBE: No result'
        
    
