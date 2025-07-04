"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
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
import requests
import cv2 as cv
import os
import io
from time import sleep, time
from zipfile import ZipFile, ZIP_DEFLATED
from setproctitle import setproctitle
from logging import getLogger
from django.utils import timezone
from camai.version import version
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "camai.settings")
django.setup()
from tools.l_tools import djconf, seq_to_int
from tools.c_tools import list_from_queryset
from users.userinfo import afree_quota
from .models import trainframe
from camai.version import version

class train_once_remote():

  def __init__(self, myschool, myfit, dbline):
    self.myschool = myschool
    self.myfit = myfit
    self.t_type = dbline.t_type
    self.tainer_id = dbline.id
    self.wsurl = dbline.wsserver+'ws/remotetrainer/'
    self.wsname = dbline.wsname
    self.wspass = dbline.wspass
    self.modeltype = dbline.modeltype

  def send_ping(self):
    if time() - self.ws_ts < 2.0:
      return()
    while True:
      try:
        self.ws.send('Ping', opcode=1)
        self.ws_ts = time()
        break
      except BrokenPipeError:
        self.logger.warning('Socket error while pinging prediction server')
        sleep(djconf.getconfigfloat('medium_brake', 0.1))

  def run(self):
    from tools.c_logger import log_ini
    setproctitle('CAM-AI-Rem-Train #'+str(self.tainer_id))
    self.logname = 'rem_train #'+str(self.tainer_id)
    self.logger = getLogger(self.logname)
    log_ini(self.logger, self.logname)
    self.logger.info('****************************************************');
    self.logger.info('*** Working on School #'
      +str(self.myschool.id)+', '+self.myschool.name+'...');
    self.logger.info('****************************************************');
    from websocket import WebSocket #, enableTrace
    from websocket._exceptions import WebSocketConnectionClosedException
    #enableTrace(True)
    self.ws = WebSocket()
    self.ws.connect(self.wsurl)
    outdict = {
      'code' : 'auth',
      'name' : self.wsname,
      'pass' : self.wspass,
      'school' : self.myschool.e_school,
      'version' : version,
    }
    while True:
      try:
        self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
        break
      except BrokenPipeError:
        self.logger.warning('Socket error while pushing initialization data '
          + 'to training server')
        sleep(djconf.getconfigfloat('medium_brake', 0.1))
    self.ws.recv()    
    outdict = {
      'code' : 'init_trainer',
      'school' : self.myschool.e_school,
      'version' : version,
    } 
    self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
    result = json.loads(self.ws.recv())
    if result['status'] != 'OK':
      return(1)
    model_in_dims = result['dims']
    outdict = {
      'code' : 'namecheck',
      'school' : self.myschool.e_school,
    } 
    self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
    remoteset = set()
    remoteset_with_size = set()
    remotedict = {}
    remotelist = []
    while True:
      if (item := json.loads(self.ws.recv())) == 'done':
        break
      remotelist.append(item)
    for item in remotelist:
      remotedict[item[0]] = item[1]
      remoteset.add(item[0])
      if item[2]:
        remoteset_with_size.add(item[0])
    self.ws_ts = time()
    filterdict = {
      'school' : self.myschool.id, 
      'deleted' : False,
    }
    if not self.myschool.ignore_checked:
      filterdict['checked'] = True
    localsearch = list_from_queryset(trainframe.objects.filter(**filterdict))
    localset = set()
    localdict = {}
    for item in localsearch:
      localdict[item.name] = [item.c0, item.c1, item.c2, item.c3, item.c4, 
        item.c5, item.c6, item.c7, item.c8, item.c9, ]
      localdict[item.name] += [seq_to_int(localdict[item.name])]
      localdict[item.name] += [item.code]
      localset.add(item.name)
    count = len(remoteset & localset)
    for item in (remoteset & localset):
      if remotedict[item] != localdict[item][10]:
        self.logger.info('(' + str(count) + ') Changed, deleting: ' + item)
        remoteset.remove(item)
      count -= 1  
      self.send_ping()
    count = len(remoteset - localset)
    for item in (remoteset - localset):
      self.logger.info('(' + str(count) + ') Deleting: ' + item)
      outdict = {
        'code' : 'delete',
        'name' : item,
      }
      self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
      i = 0
      while i < 20:
        try:
          self.ws.recv()
          break
        except TimeoutError:
          i += 1
      count -= 1
      self.send_ping()

    datalist = list(localset - remoteset_with_size) 
    count = len(datalist)
    start = 0
    step = 100
    for i in range(start, len(datalist), step):
      sublist = datalist[i:i+step]
      zip_buffer = io.BytesIO()   
      with ZipFile(zip_buffer, 'a', ZIP_DEFLATED) as zip_file:
        for item in sublist:
          imagedata = cv.imread(self.myschool.dir + 'frames/' + item)
          if imagedata.shape[1] > model_in_dims[0] or imagedata.shape[0] > model_in_dims[1]:
            imagedata = cv.resize(imagedata, model_in_dims)
          imagedata = cv.imencode('.jpg', imagedata)[1].tobytes()
          zip_file.writestr(item, io.BytesIO(imagedata).getvalue())
          jsondata = json.dumps(localdict[item]).encode()
          zip_file.writestr(item + '.json', io.BytesIO(jsondata).getvalue())
          self.logger.info('(' + str(count) + ') Zipped for sending: ' + item)
          count -= 1  
      zip_buffer.seek(0)
      zip_content = zip_buffer.read()
      self.ws.send_binary(zip_content)
      self.ws.recv()
      self.send_ping()
    if self.t_type == 2:
      outdict = {
        'code' : 'checkfitdone',
        'mode' : 'init',
        'school' : self.myschool.e_school,
      }
      self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
      temp = self.ws.recv()
      model_type = json.loads(temp)
    outdict = {
      'code' : 'trainnow',
    } 
    self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
    self.logger.info('Sent trigger for train_now... ')
    if self.t_type == 2:
      outdict = {
        'code' : 'checkfitdone',
        'mode' : 'sync',
        'school' : self.myschool.e_school,
      }
      self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
      dlurl = json.loads(self.ws.recv())
      self.logger.info('DL Url: ' + dlurl)
      outdict = {
        'code' : 'checkfitdone',
        'mode' : 'check',
        'school' : self.myschool.e_school,
      }
      while True:
        while True:
          try:
            self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
            result = json.loads(self.ws.recv())
            break
          except  WebSocketConnectionClosedException:
            self.logger.info('Reconnecting Websocket while waiting... ')
            sleep(10.0)
            self.ws.connect(self.wsurl)
        if result:
          break
        else:
          sleep(10.0)
          
    outdict = {
      'code' : 'close_ws',
    }
    self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
    self.ws.recv()
    #sleep(2.0)
    self.ws.close()
          
    if self.t_type == 2:
      if self.modeltype == 1:
        dlurl += 'K/'
      elif self.modeltype == 2:
        dlurl += 'L/'
      elif self.modeltype == 3:
        dlurl += 'Q/'
      r = requests.get(dlurl, allow_redirects=True)
      datapath = djconf.getconfig('datapath', 'data/')
      dlfile = djconf.getconfig('schools_dir', datapath + 'schools/')
      dlfile += 'model' + str(self.myschool.id) + '/model/'
      if self.modeltype == 1:
        dlfile += model_type + '.keras'
      else:
        dlfile += model_type + '.tflite'
      self.logger.info('DL Model: ' + dlfile)
      open(dlfile, 'wb').write(r.content)
      self.myschool.lastmodelfile = timezone.now()
      self.myschool.save(update_fields=["lastmodelfile"])
    self.logger.info('Done...')
    return(0)
