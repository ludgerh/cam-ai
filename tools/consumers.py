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

from pathlib import Path
from time import time, sleep
from json import loads, dumps
from subprocess import Popen, PIPE
from logging import getLogger
from ipaddress import ip_network, ip_address
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM, gethostbyaddr, herror, gaierror
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from tools.c_logger import log_ini
from tools.djangodbasync import getonelinedict, filterlinesdict, deletefilter, updatefilter, savedbline
from tools.l_tools import djconf
from tf_workers.models import school
from trainers.models import trainframe
from eventers.models import event, event_frame
from streams.c_streams import streams, c_stream
from streams.models import stream as dbstream
from streams.startup import start_stream_list

logname = 'ws_toolsconsumers'
logger = getLogger(logname)
log_ini(logger, logname)
recordingspath = Path(djconf.getconfig('recordingspath', 'data/recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', 'data/schoolframes/'))

s = socket(AF_INET, SOCK_DGRAM)
subnetmask = '255.255.255.0'
try:
  s.connect(('10.255.255.255', 1))
  my_ip = s.getsockname()[0]
except Exception:
  my_ip = '127.0.0.1'
finally:
  s.close()
my_net = ip_network(my_ip+'/'+subnetmask, strict=False)
my_ip = ip_address(my_ip)

#*****************************************************************************
# health
#*****************************************************************************

class health(AsyncWebsocketConsumer):

  async def connect(self):
    if self.scope['user'].is_superuser:
      self.filesetdict = {}
      self.dbsetdict = {}
      self.countdict = {}
      await self.accept()
    else:
      await self.close()

  async def receive(self, text_data):
    logger.debug('<-- ' + text_data)
    params = loads(text_data)['data']	
    outlist = {'tracker' : loads(text_data)['tracker']}	

    if params['command'] == 'checkschool':
      myschool = await getonelinedict(school, {'id' : params['school'], }, ['dir'])
      self.filesetdict[params['school']] = {item.name for item in (Path(myschool['dir']) / 'frames').iterdir()}
      dbset = await filterlinesdict(trainframe, {'school' : params['school'], }, ['name'])
      self.dbsetdict[params['school']] = {item['name'][7:] for item in dbset}
      outlist['data'] = {
        'correct' : len(self.filesetdict[params['school']] & self.dbsetdict[params['school']]),
        'missingdb' : len(self.filesetdict[params['school']] - self.dbsetdict[params['school']]),
        'missingfiles' : len(self.dbsetdict[params['school']] - self.filesetdict[params['school']]),
      }
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingdb':	
      myschool = await getonelinedict(school, {'id' : params['school'], }, ['dir'])
      for item in (self.filesetdict[params['school']] - self.dbsetdict[params['school']]):
        (Path(myschool['dir']) / 'frames' / item).unlink()
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingfiles':	
      for item in (self.dbsetdict[params['school']] - self.filesetdict[params['school']]):
        await deletefilter(trainframe, {'name' : 'frames/'+item, })	
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'checkrecfiles':
      fileset = [item for item in recordingspath.iterdir()]
      self.fileset_c = [item.name for item in fileset if (
        item.name[0] == 'C' 
        and item.suffix == '.mp4'
        and item.exists()
        and item.stat().st_mtime < (time() - 1800)
      )]
      fileset_jpg = {item.stem for item in fileset if (item.name[:2] == 'E_') and (item.suffix == '.jpg')}
      fileset_mp4 = {item.stem for item in fileset if (item.name[:2] == 'E_') and (item.suffix == '.mp4')}
      self.fileset = fileset_jpg & fileset_mp4
      self.fileset_all = fileset_jpg | fileset_mp4
      mydbset = await filterlinesdict(event, {'videoclip__startswith' : 'E_',}, ['videoclip', 'start', ])
      self.dbset = set()
      self.dbtimedict = {}
      for item in mydbset:
        self.dbset.add(item['videoclip'])
        self.dbtimedict[item['videoclip']] = item['start']
      outlist['data'] = {
        'jpg' : len(fileset_jpg),
        'mp4' : len(fileset_mp4),
        'temp' : len(self.fileset_c),
        'correct' : len(self.fileset & self.dbset),
        'missingdb' : len(self.fileset_all - self.dbset),
        'missingfiles' : len(self.dbset - self.fileset),
      }
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixtemp_rec':	
      for item in (self.fileset_c):
        if (recordingspath / item).exists():
          (recordingspath / item).unlink()
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingdb_rec':	
      for item in (self.fileset_all - self.dbset):
        for ext in ['.jpg', '.mp4']:
          delpath = recordingspath / (item+ext)
          if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
            delpath.unlink()
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingfiles_rec':	
      for item in (self.dbset - self.fileset):
        if self.dbtimedict[item].timestamp()  < (time() - 1800):
          await updatefilter(event, {'videoclip' : item, }, {'videoclip' : '', }) 
          for ext in ['.jpg', '.mp4']:
            delpath = recordingspath / (item+ext)
            if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
              delpath.unlink()
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'checkevents':
      self.eventframeset = await filterlinesdict(event_frame, None, ['event'])
      self.eventframeset = {item['event'] for item in self.eventframeset}
      self.eventset = await filterlinesdict(event, None, ['id'])
      self.eventset = {item['id'] for item in self.eventset}
      outlist['data'] = {
        'correct' : len(self.eventset & self.eventframeset),
        'missingevents' : len(self.eventframeset - self.eventset),
        'missingframes' : len(self.eventset - self.eventframeset),
      }
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingevents':	
      #not implemented. This case is not possible because of database logic
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingframes':	
      for item in (self.eventset - self.eventframeset):
        try:
          eventdict = await getonelinedict(event, {'id' : item, }, ['videoclip', 'start', ]) 
          if (len(eventdict['videoclip']) < 3) and (eventdict['start'].timestamp()  < (time() - 1800)):
            await deletefilter(event, {'id' : item, })
          else:
            await updatefilter(event, {'id' : item, }, {'numframes' : 0, })
        except event.DoesNotExist:
          pass
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'checkframes':
      self.framefileset = {item.relative_to(schoolframespath).as_posix() for item in schoolframespath.rglob('*.bmp')}
      self.framedbset = await filterlinesdict(event_frame, None, ['name'])
      self.framedbset = {item['name'] for item in self.framedbset}
      outlist['data'] = {
        'correct' : len(self.framefileset & self.framedbset),
        'missingdblines' : len(self.framefileset - self.framedbset),
        'missingfiles' : len(self.framedbset - self.framefileset),
      }
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingframesdb':	
      for item in (self.framefileset - self.framedbset):
        delpath = schoolframespath / item
        if (delpath.exists() and  delpath.stat().st_mtime < (time() - 1800)):
          delpath.unlink()
          countpath = delpath.parent
          myindex = countpath.parent.name+'_'+countpath.name
          if myindex in self.countdict:
            self.countdict[myindex] -= 1
            mycount = self.countdict[myindex]
          else:
            mycount = len(list(countpath.iterdir()))
            self.countdict[myindex] = mycount
          if mycount == 0:
            countpath.rmdir()
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'fixmissingframesfiles':	
      for item in (self.framedbset - self.framefileset):
        try:
          framedict = await getonelinedict(event_frame, {'name' : item, }, ['time', ]) 
          if framedict['time'].timestamp()  < (time() - 1800):
            await deletefilter(event_frame, {'name' : item, })
        except event.DoesNotExist:
          pass
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

#*****************************************************************************
# admintools
#*****************************************************************************

def scanoneip(ipstring, myports):
  portlist = []
  for port in myports:
    s = socket(AF_INET, SOCK_STREAM)
    s.settimeout(0.2)
    try:
      result = s.connect_ex((ipstring, port))
    except gaierror:
      return(None)
    s.close()
    if result == 0:
      portlist.append(port)
  if portlist:
    result = {}
    result['ip'] = ipstring
    try:
      result['name'] = gethostbyaddr(ipstring)[0]
    except herror:
      result['name'] = 'name unknown'
    result['ports'] = portlist
    return(result)
  else:
    return(None)  

class admintools(AsyncWebsocketConsumer):

  async def connect(self):
    if self.scope['user'].is_superuser:
      await self.accept()
    else:
      await self.close()

  async def receive(self, text_data):
    logger.debug('<-- ' + text_data)
    params = loads(text_data)['data']	
    outlist = {'tracker' : loads(text_data)['tracker']}	

    if params['command'] == 'scanoneip':
      if params['portaddr'] == 554:
        cmds = ['ffprobe', '-v', 'fatal', '-print_format', 'json', 
          '-rtsp_transport', 'tcp', '-show_streams', params['camurl']]
      else:
        cmds = ['ffprobe', '-v', 'fatal', '-print_format', 'json', 
          '-show_streams', params['camurl']]
      p = Popen(cmds, stdout=PIPE)
      output, _ = p.communicate()
      outlist['data'] = loads(output)
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'scanips':
      if params['portaddr']:
        portlist = [params['portaddr'], ]
      else:
        portlist = [80, 443, 554, 1935, ]
      contactlist = []
      for item in my_net.hosts():        
        if item != my_ip:
          if (checkresult := scanoneip(str(item), portlist)):
            contactlist.append(checkresult)
      outlist['data'] = contactlist
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

    elif params['command'] == 'installcam':
      newstream = dbstream()
      newstream.cam_url = params['camurl']
      newstream.cam_video_codec = params['videocodec']
      newstream.cam_audio_codec = params['audiocodec']
      await savedbline(newstream)
      while start_stream_list:
        sleep(djconf.getconfigfloat('long_brake', 1.0))
      start_stream_list.add(newstream.id)

      outlist['data'] = {'id' : newstream.id, }
      logger.debug('--> ' + str(outlist))
      await self.send(dumps(outlist))	

