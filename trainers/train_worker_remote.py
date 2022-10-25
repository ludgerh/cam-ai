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

import json
from time import sleep, time
from multitimer import MultiTimer
from traceback import format_exc
from tools.l_tools import djconf
from .models import trainframe

class train_once_remote():

  def __init__(self, myschool, myfit, wsserver, logger):
    self.myschool = myschool
    self.myfit = myfit
    self.logger = logger
    self.wsurl = wsserver+'ws/remotetrainer/'
    self.ws_ts = None

  def send_ping(self):
    while True:
      try:
        self.ws.send('Ping', opcode=1)
        self.ws_ts = time()
        break
      except BrokenPipeError:
        self.logger.warning('Socket error while pinging prediction server')
        sleep(djconf.getconfigfloat('medium_brake', 0.1))

  def run(self):
    try:
      self.logger.info('*******************************************************');
      self.logger.info('*** Working on School #'
        +str(self.myschool.id)+', '+self.myschool.name+'...');
      self.logger.info('*******************************************************');
      from websocket import WebSocket #, enableTrace
      #enableTrace(True)
      self.ws = WebSocket()
      self.ws.connect(self.wsurl)
      outdict = {
        'code' : 'auth',
        'name' : self.myschool.tf_worker.wsname,
        'pass' : self.myschool.tf_worker.wspass,
      }
      while True:
        try:
          self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
          break
        except BrokenPipeError:
          self.logger.warning('Socket error while pushing initialization data '
            + 'to training server')
          sleep(djconf.getconfigfloat('medium_brake', 0.1))


      outdict = {
        'code' : 'namecheck',
        'school' : self.myschool.e_school,
      } 
      self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
      remoteset = set(json.loads(self.ws.recv()))
      self.ws_ts = time()
      pingproc = MultiTimer(interval=2, function=self.send_ping, runonstart=False)
      pingproc.start()
      filterdict = {'school' : self.myschool.id, }
      if not self.myschool.ignore_checked:
        filterdict['checked'] = True
      localsearch = trainframe.objects.filter(**filterdict)
      localset = set()
      localdict = {}
      for item in localsearch:
        localdict[item.name] = (item.c0, item.c1, item.c2, item.c3, item.c4, item.c5, item.c6, item.c7, item.c8, item.c9, )
        localset.add(item.name)
      pingproc.stop()
      for item in (remoteset - localset):
        outdict = {
          'code' : 'delete',
          'name' : item,
        }
        self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
        self.logger.info('Deleting: ' + item)
      for item in (localset - remoteset):
        outdict = {
          'code' : 'send',
          'name' : item,
          'tags' : localdict[item]
        }
        self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
        self.logger.info('Sending: ' + item)
        filepath = self.myschool.dir + item
        with open(filepath, "rb") as f:
          self.ws.send_binary(f.read())
      outdict = {
        'code' : 'trainnow',
      } 
      self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
      self.ws.close()
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()
    return(True)
