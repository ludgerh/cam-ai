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
from time import time
from json import loads, dumps
from logging import getLogger
from channels.generic.websocket import AsyncWebsocketConsumer
from tools.c_logger import log_ini
from tools.djangodbasync import getonelinedict, filterlinesdict, deletefilter, updatefilter
from tools.l_tools import djconf
from tf_workers.models import school
from trainers.models import trainframe
from eventers.models import event, event_frame

logname = 'ws_toolsconsumers'
logger = getLogger(logname)
log_ini(logger, logname)
recordingspath = Path(djconf.getconfig('recordingspath', 'data/recordings/'))
schoolframespath = Path(djconf.getconfig('schoolframespath', 'data/schoolframes/'))

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
