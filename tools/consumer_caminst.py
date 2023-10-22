import json
#from pprint import pprint
from logging import getLogger
from ipaddress import ip_network, ip_address
from subprocess import Popen, PIPE
from time import sleep
from tools.djangodbasync import filterlinesdict, savedbline
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini
from tools.c_redis import myredis
from tools.l_tools import djconf
from streams.c_camera import get_ip_address, get_ip_network, search_executor
from streams.c_streams import streams
from tf_workers.models import school
from streams.models import stream as dbstream
from access.models import access_control


logname = 'ws_caminst'
logger = getLogger(logname)
log_ini(logger, logname)

redis = myredis()

long_brake = djconf.getconfigfloat('long_brake', 1.0)

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
    if self.scope['user'].is_superuser:
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
      if 'ipaddress' in params:
        myip = ip_network(params['ipaddress'])
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
        max_workers=100,
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
      newstream.cam_video_codec = params['videocodec']
      if params['audiocodec'] is None:
        newstream.cam_audio_codec = -1
      else:  
        newstream.cam_audio_codec = params['audiocodec']
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
      while redis.get_start_stream_busy():
        sleep(long_brake)
      redis.set_start_stream_busy(newstream.id)
      while (not (newstream.id in streams)):
        sleep(long_brake)
      outlist['data'] = {'id' : newstream.id, }
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	
