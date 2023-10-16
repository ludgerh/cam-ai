import json
#from pprint import pprint
from logging import getLogger
from ipaddress import ip_network, ip_address
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini
from streams.c_camera import get_ip_address, get_ip_network, search_executor


logname = 'ws_caminst'
logger = getLogger(logname)
log_ini(logger, logname)

class caminst(AsyncWebsocketConsumer):

  async def connect(self):
    if self.scope['user'].is_superuser:
      self.myip = get_ip_address()
      self.mynet = get_ip_network(self.myip)
      await self.accept()

  async def receive(self, text_data):
    logger.info('<-- ' + text_data)
    params = json.loads(text_data)['data']	
    outlist = {'tracker' : json.loads(text_data)['tracker']}	

    if params['command'] == 'getnetandip':
      outlist['data'] = {
        'mynet' : str(self.mynet),
        'myip' : str(self.myip),
      }
      logger.info('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    if params['command'] == 'scanips':
      e = search_executor(
        net=ip_network(params['network']), 
        ip=ip_address(params['ipaddr']), 
        ports=params['portaddr'], 
        url=params['camaddress'], 
        max_workers=100,
      )
      #pprint(e.all_results)
      outlist['data'] = e.all_results
      logger.info('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	
