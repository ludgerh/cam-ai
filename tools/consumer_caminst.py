# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
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
#from pprint import pprint
from logging import getLogger
from ipaddress import ip_network, ip_address
from subprocess import Popen, PIPE
from time import sleep
from validators.domain import domain
from validators.ip_address import ipv4, ipv6
from tools.djangodbasync import filterlinesdict, savedbline, getonelinedict, countfilter
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini
from tools.c_redis import myredis
from tools.l_tools import djconf
from streams.c_camera import get_ip_address, get_ip_network, search_executor
from streams.c_streams import streams
from tf_workers.models import school
from streams.models import stream as dbstream
from users.models import userinfo
from access.models import access_control
from access.c_access import access


logname = 'ws_caminst'
logger = getLogger(logname)
log_ini(logger, logname)

redis = myredis()

long_brake = djconf.getconfigfloat('long_brake', 1.0)
is_public_server = djconf.getconfigbool('is_public_server', False)

class caminst(AsyncWebsocketConsumer):
    
  async def check_create_stream_priv(self):
    if self.scope['user'].is_superuser:
      return(True)
    else:
      limit = await getonelinedict(
        userinfo, 
        {'user' : self.scope['user'].id, }, 
        ['allowed_streams',]
      )
      limit = limit['allowed_streams']
      streamcount = await countfilter(
        dbstream, 
        {'creator' : self.scope['user'].id, 'active' : True,},
      )
      return(streamcount < limit)  
    

  async def connect(self):
    self.myip = get_ip_address()
    self.mynet = get_ip_network(self.myip)
    await self.accept()

  async def receive(self, text_data):
    logger.debug('<-- ' + text_data)
    params = json.loads(text_data)['data']	
    outlist = {'tracker' : json.loads(text_data)['tracker']}	

    if params['command'] == 'getnetandip':
      outlist['data'] = {
        'mynet' : str(self.mynet),
        'myip' : str(self.myip),
      }
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'scanips':
      if 'network' in params:
        mynet = ip_network(params['network'])
      else:
        mynet = None  
      if 'ipaddr' in params:
        myip = params['ipaddr']
      else:
        myip = None  
      if 'uname' in params:
        myname = params['uname']
      else:
        myname = '' 
      if 'upass' in params:
        mypass = params['upass']
      else:
        mypass = ''
      e = search_executor(
        net=mynet, 
        ip=myip, 
        uname = myname,
        upass = mypass,
        ports=params['portaddr'], 
        url=params['camaddress'], 
        max_workers=20,
      )
      #pprint(e.all_results)
      outlist['data'] = e.all_results
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	
      
    elif params['command'] == 'scanoneip':
      if not await self.check_create_stream_priv():
        await self.close()
      cmds = ['ffprobe', '-v', 'fatal', '-print_format', 'json', 
        '-show_streams', params['camurl']]
      p = Popen(cmds, stdout=PIPE)
      output, _ = p.communicate()
      outlist['data'] = json.loads(output)
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'installcam':
      if not await self.check_create_stream_priv():
        await self.close()
      myschools = await filterlinesdict(school, {'active' : True, }, ['id', ])
      myschool = myschools[0]['id']
      newstream = dbstream()
      if 'name' in params:
        newstream.name = params['name']
      newstream.cam_url = params['camurl']
      # cam_video_codec and cam_audio_codec are set to -1 (auto)
      # should be put to values from params
      newstream.cam_video_codec = -1
      newstream.cam_audio_codec = -1
      #newstream.cam_video_codec = params['videocodec']
      #if params['audiocodec'] is None:
      #  newstream.cam_audio_codec = -1
      #else:  
      #  newstream.cam_audio_codec = params['audiocodec']
      newstream.name = params['cam_name']
      newstream.cam_xres = params['xresolution']
      newstream.cam_yres = params['yresolution']
      newstream.cam_control_mode = params['control_mode']
      newstream.cam_control_user = params['control_user']
      newstream.cam_control_passwd = params['control_pass']
      newstream.cam_control_ip = params['control_ip']
      newstream.cam_control_port = params['control_port']
      newstream.eve_school_id = myschool
      newstream.creator = self.scope['user']
      newlineid = await savedbline(newstream)
      if not self.scope['user'].is_superuser:
        myaccess = access_control()
        myaccess.vtype = 'X'
        myaccess.vid = newlineid
        myaccess.u_g_nr = self.scope['user'].id
        myaccess.r_w = 'W'
        await savedbline(myaccess)
        await access.read_list_async()
      while redis.get_start_stream_busy():
        sleep(long_brake)
      redis.set_start_stream_busy(newstream.id)
      while (not (newstream.id in streams)):
        sleep(long_brake)
      outlist['data'] = {'id' : newstream.id, }
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'validate_domain':
      mydomain = params['domain']
      if '//' in mydomain:
        mydomain = mydomain.split('//')[1]
      if '/' in mydomain:
        mydomain = mydomain.split('/')[0]  
      if (mydomain == '') and self.scope['user'].is_superuser:
        result = True #Admin may scan the network
      elif domain(mydomain):  
        result = True #Anyone may check an external domain
      elif ipv4(mydomain) or ipv6(mydomain):
        result = not is_public_server #IPs permitted on Raspis, not Eygelshoven
      else:
        result = False #No correct IP nor domain
      outlist['data'] = {'result' : result, 'domain' : mydomain, } 
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	
      
