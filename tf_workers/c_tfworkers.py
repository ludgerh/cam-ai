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
import numpy as np
import cv2 as cv
from os import environ, path, makedirs
from multiprocessing import Process, Queue
from collections import deque
from time import sleep, time
from threading import Thread, Lock, get_native_id
from random import random
from traceback import format_exc
from logging import getLogger
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from inspect import currentframe, getframeinfo, stack
from websocket._exceptions import (WebSocketTimeoutException, 
  WebSocketConnectionClosedException,
  WebSocketBadStatusException, 
)
from django.db.utils import OperationalError
from django.db import connections, connection
from tools.l_tools import QueueUnknownKeyword, djconf, get_proc_name
from tools.c_tools import cmetrics, hit100
from tools.c_logger import log_ini
from .models import school, worker
from schools.c_schools import get_taglist

tf_workers = {}
for item in school.objects.filter(active=True):
  if not item.dir:
    item.dir = (djconf.getconfig('schools_dir', 'data/schools/model') 
      + str(item.id) + '/')
    item.save(update_fields=['dir',]) 
  if not path.exists(item.dir):
    makedirs(item.dir)
taglist = get_taglist(1)

#***************************************************************************
#
# tools common
#
#***************************************************************************

def sigint_handler(signal, frame):
  #print ('TFWorkers: Interrupt is caught')
  pass

#***************************************************************************
#
# tools server
#
#***************************************************************************

class model_buffer(deque):

  def __init__(self, schoolnr, xdim, ydim):
    super().__init__()
    self.ts = time()
    self.xdim = xdim
    self.ydim = ydim
    self.bufferlock1 = Lock()
    self.bufferlock2 = Lock()

  def append(self, initem):
    # structure of initem:
    # initem[0] = np.imagelist, initem[1] = userindex,
    # initem[2] = frame_id_list, iniitem[3] = eventnr
    # structure of list outitem:
    # outitem[0] = np.image, outitem[1] = userindex,
    # outitem[2] = frame_id, outitem[3] = entnr
    framecount = initem[0].shape[0]
    imagelist = np.vsplit(initem[0], framecount)
    with self.bufferlock1:
      for i in range(framecount):
        outitem = [imagelist[i]]
        outitem.append(initem[1])
        if initem[2]:
          outitem.append(initem[2][i])
        else:
          outitem.append(-1)
        outitem.append(initem[3])
        super().append(outitem)
    self.ts = time()

  def get(self, maxcount):
    tempres0 = []
    tempres1 = []
    tempres2 = []
    tempres3 = []
    while True:
      with self.bufferlock1:
        if not len(self):
          break
        initem = self.popleft()
      tempres0.append(initem[0])
      tempres1.append(initem[1])
      tempres2.append(initem[2])
      tempres3.append(initem[3])
      if len(tempres0) >= maxcount:
        break
    return(np.vstack(tempres0), tempres1, tempres2, tempres3)

class tf_user(object):

  def __init__(self, clientset, clientlock):
    self.clientset = clientset
    self.clientlock = clientlock
    with self.clientlock:
      i = 0
      while not (i in self.clientset):
        i += 1
      self.clientset.discard(i)
      self.id = i

  def __del__(self):
    with self.clientlock:
      self.clientset.add(self.id)

#***************************************************************************
#
# tf_worker common
#
#***************************************************************************

class tf_worker():
  def __init__(self, idx):
    #*** Common Vars
    self.id = idx
    self.dbline = worker.objects.get(id=self.id)
    if (self.dbline.gpu_sim < 0) and (not self.dbline.use_websocket): #Local GPU
      environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
      environ["CUDA_VISIBLE_DEVICES"]=str(self.dbline.gpu_nr)
      import tensorflow as tf
      gpus = tf.config.list_physical_devices('GPU')
      if gpus:
        for gpu in gpus:
          tf.config.experimental.set_memory_growth(gpu, True)
        #tf.config.experimental.set_visible_devices(gpus[self.dbline.gpu_nr], 'GPU')
      from tensorflow.keras.models import load_model
      self.load_model = load_model
      self.tf = tf

    self.inqueue = Queue()
    self.registerqueue = Queue()
    self.outqueues = {}
    for i in range(self.dbline.max_nr_clients):
      self.outqueues[i] = Queue()
    self.is_ready = False

    #*** Server Var
    self.myschool_cache = {}
    self.allmodels = {}
    self.activemodels = {}
    self.modelschecked = set()

    #*** Client Var
    self.run_out_procs = {}
    self.pred_out_dict = {}
    self.mylock = Lock()
    self.very_short_brake = djconf.getconfigfloat('very_short_brake', 0.001)
    self.ws_ts = None

  def send_ping(self):
    if self.ws_ts is None:
      return()
    if (time() - self.ws_ts) > 15:
      while True:
        try:
          self.ws.send('Ping', opcode=1)
          self.ws_ts = time()
          break
        except (ConnectionResetError, OSError, BrokenPipeError):
          sleep(djconf.getconfigfloat('long_brake', 1.0))
          self.reset_websocket()

  def reset_websocket(self):
    from websocket import WebSocket #, enableTrace
    #enableTrace(True)
    while self.do_run:
      try:
        self.ws_ts = time()
        self.ws = WebSocket()
        self.ws.connect(self.dbline.wsserver+'ws/predictions/')
        outdict = {
          'code' : 'auth',
          'name' : self.dbline.wsname,
          'pass' : self.dbline.wspass,
          'server_nr' : djconf.getconfigint('system_number'),
          'worker_nr' : self.id,
          'soft_ver' : djconf.getconfig('version', 'not set'),
        }
        self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
        break
      except (BrokenPipeError, 
            TimeoutError,
            WebSocketBadStatusException, 
            ConnectionRefusedError,
            OSError,
          ):
        self.logger.warning('BrokenPipe or Timeout while resetting prediction websocket server')
        sleep(djconf.getconfigfloat('long_brake', 1.0))

  def continue_sending(self, payload, opcode=1, logger=None, get_answer=False):
    while self.do_run:
      while self.do_run:
        try:
          if opcode:
            self.ws.send(payload, opcode=1) # 1 = Text
            frameinfo = getframeinfo(currentframe())
          else:
            self.ws.send_binary(payload) # 0 = Bytes
            frameinfo = getframeinfo(currentframe())
          break
        except (BrokenPipeError,
              WebSocketBadStatusException,
            ):
          if logger:
            frameinfo = getframeinfo(currentframe())
            logger.warning('Pipe error while sending in ' + frameinfo.filename + ':' + str(frameinfo.lineno))
          sleep(djconf.getconfigfloat('long_brake', 1.0))
          self.reset_websocket()
      if get_answer:
        try:
          return(self.ws.recv())
        except (WebSocketTimeoutException, 
              WebSocketConnectionClosedException, 
              ConnectionRefusedError,
            ):
          if logger:
            logger.warning('Pipe error while reading in ' + frameinfo.filename + ':' + str(frameinfo.lineno))
          sleep(djconf.getconfigfloat('long_brake', 1.0))
          self.reset_websocket()
      else:
        return(None)
    

#***************************************************************************
#
# tf_worker server
#
#***************************************************************************

  def in_queue_thread(self):
    try:
      while True:
        received = self.inqueue.get()
        #print('TFW in', received)
        if (received[0] == 'stop'):
          self.do_run = False
          while not self.inqueue.empty():
            received = self.inqueue.get()
          break
        elif (received[0] == 'unregister'):
          if received[1] in self.users:
            del self.users[received[1]]
        elif (received[0] == 'get_is_ready'):
          self.outqueues[received[1]].put(('put_is_ready', self.is_ready))
        elif (received[0] == 'get_xy'):
          if self.dbline.use_websocket:
            self.check_model(received[1], self.logger)
            xdim = self.allmodels[received[1]]['xdim']
            ydim = self.allmodels[received[1]]['ydim']
          else:
            self.check_model(received[1], self.logger)
            xdim = self.allmodels[received[1]]['xdim']
            ydim = self.allmodels[received[1]]['ydim']
          self.outqueues[received[2]].put(('put_xy', (xdim, ydim)))
        elif (received[0] == 'imglist'):
          schoolnr = received[1]
          if schoolnr not in self.model_buffers:
            self.check_model(schoolnr, self.logger)
            self.model_buffers[schoolnr] = model_buffer(schoolnr, 
              self.allmodels[schoolnr]['xdim'], 
              self.allmodels[schoolnr]['ydim'])
          self.model_buffers[schoolnr].append(received[2:])
          with self.model_buffers[schoolnr].bufferlock2:
            while len(self.model_buffers[schoolnr]) >= self.dbline.maxblock:
              self.process_buffer(schoolnr, self.logger)
        elif (received[0] == 'register'):
          myuser = tf_user(self.clientset, self.clientlock)
          self.users[myuser.id] = myuser
          self.registerqueue.put(myuser.id)
        elif (received[0] == 'checkmod'):
          self.check_model(received[1], self.logger, received[2])
        else:
          raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def runner(self):
    self.dbline = worker.objects.get(id=self.id)
    self.clientset = set(range(self.dbline.max_nr_clients))
    self.clientlock = Lock()
    self.users = {}
    Thread(target=self.in_queue_thread, name='TFW_InQueueThread').start()
    signal(SIGINT, sigint_handler)
    signal(SIGTERM, sigint_handler)
    signal(SIGHUP, sigint_handler)
    self.logname = 'tf_worker #'+str(self.dbline.id)
    self.logger = getLogger(self.logname)
    log_ini(self.logger, self.logname)
    try:
      setproctitle('CAM-AI-TFWorker #'+str(self.dbline.id))
      self.model_buffers = {}
      if self.dbline.gpu_sim >= 0:
        self.cachedict = {}
      elif self.dbline.use_websocket:
        self.reset_websocket()
      self.is_ready = True
      schoolnr = -1
      while (len(self.model_buffers) == 0) and self.do_run:
        if self.dbline.use_websocket:
          self.send_ping()
        sleep(djconf.getconfigfloat('long_brake', 1.0))
      self.finished = False
      while self.do_run:
        if self.dbline.use_websocket:
          self.send_ping()
        while self.do_run:
          schoolnr += 1
          if schoolnr > max(self.model_buffers):
            schoolnr = 1
          if schoolnr in self.model_buffers:
            break
        if self.do_run:
          with self.model_buffers[schoolnr].bufferlock2:
            run_ok = (
              ((self.model_buffers[schoolnr].ts + self.dbline.timeout) < time()) 
              and len(self.model_buffers[schoolnr]))
            if run_ok:
              self.process_buffer(schoolnr, self.logger, had_timeout=True)
          if not run_ok:
            sleep(djconf.getconfigfloat('short_brake', 0.01))
      self.finished = True
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()
    self.logger.info('Finished Process '+self.logname+'...')
    self.logger.handlers.clear()

  def run(self):
    self.do_run = True
    self.run_process = Process(target=self.runner)
    connections.close_all()
    self.run_process.start()

  def check_model(self, schoolnr, logger, test_pred = False):
    if schoolnr in self.modelschecked:
      return()
    self.modelschecked.add(schoolnr)
    if (self.dbline.gpu_sim < 0) and (not self.dbline.use_websocket): #Local GPU
      if ((schoolnr in self.myschool_cache) 
          and (self.myschool_cache[schoolnr][1] > (time() - 60))):
        myschool = self.myschool_cache[schoolnr][0]
      else:
        while True:
          try:
            myschool = school.objects.get(id=schoolnr)
            break
          except OperationalError:
            connection.close()
        self.myschool_cache[schoolnr] = (myschool, time())
      if schoolnr in self.allmodels:
        if ((myschool.lastmodelfile is not None)
            and	((self.allmodels[schoolnr]['time'] is None)
            or (myschool.lastmodelfile > self.allmodels[schoolnr]['time']))):
          del self.allmodels[schoolnr]
          del self.activemodels[schoolnr]
    if not (schoolnr in self.activemodels):
      tempmodel = None
      if not (schoolnr in self.allmodels):
        self.allmodels[schoolnr] = {}
        if (self.dbline.gpu_sim >= 0) or self.dbline.use_websocket:
          self.allmodels[schoolnr]['time'] = time()
        else:
          self.allmodels[schoolnr]['time'] = myschool.lastmodelfile
        if self.dbline.gpu_sim >= 0:
          self.allmodels[schoolnr]['xdim'] = 50
          self.allmodels[schoolnr]['ydim'] = 50
          sleep(self.dbline.gpu_sim_loading)
        elif self.dbline.use_websocket:
          myschool = school.objects.get(id=schoolnr)
          outdict = {
            'code' : 'get_xy',
            #'scho' : schoolnr,
            'scho' : myschool.e_school,
          }
          xytemp = json.loads(self.continue_sending(json.dumps(outdict), opcode=1, logger=logger, get_answer=True))
          self.allmodels[schoolnr]['xdim'] = xytemp[0]
          self.allmodels[schoolnr]['ydim'] = xytemp[1]
          sleep(self.dbline.gpu_sim_loading) 
        else: #lokal GPU
          tempmodel= self.load_model(
            myschool.dir+'model/'+myschool.model_type+'.h5', 
            custom_objects={'cmetrics': cmetrics, 'hit100': hit100,})
          self.allmodels[schoolnr]['type']=myschool.model_type
          self.allmodels[schoolnr]['xdim']=tempmodel.layers[0].input_shape[1]
          self.allmodels[schoolnr]['ydim']=tempmodel.layers[0].input_shape[2]
          self.allmodels[schoolnr]['weights'] = []
          self.allmodels[schoolnr]['weights'].append(
            tempmodel.get_layer(index=2).get_weights())
          self.allmodels[schoolnr]['weights'].append(
            tempmodel.get_layer(index=3).get_weights())
          self.allmodels[schoolnr]['weights'].append(
            tempmodel.get_layer(index=4).get_weights())
          logger.info('***** Got model file #'+str(schoolnr) 
            + ', type: '+myschool.model_type)
      if (self.dbline.gpu_sim >= 0) or self.dbline.use_websocket:
        sleep(self.dbline.gpu_sim_loading / 2)
        self.activemodels[schoolnr] = True
      else:
        if len(self.activemodels) < self.dbline.max_nr_models:
          if tempmodel is None:
            self.activemodels[schoolnr] = self.load_model(myschool.dir 
              + 'model/'+myschool.model_type+'.h5', 
              custom_objects={'cmetrics': cmetrics, 'hit100': hit100,})
          else:
            self.activemodels[schoolnr] = tempmodel
        else: #this is not tested, needed if # of models > self.max_nr_models
          nr_to_replace = min(self.activemodels, 
            key= lambda x: self.activemodels[x]['time'])	
          if self.allmodels[nr_to_replace]['type'] == myschool.model_type:
            self.activemodels[schoolnr] = self.activemodels[nr_to_replace]
            self.activemodels[schoolnr].get_layer(index=2).set_weights(
              self.allmodels[schoolnr]['weights'][0])
            self.activemodels[schoolnr].get_layer(index=3).set_weights(
              self.allmodels[schoolnr]['weights'][1])
            self.activemodels[schoolnr].get_layer(index=4).set_weights(
              self.allmodels[schoolnr]['weights'][2])
          else:
            self.activemodels[schoolnr] = load_model(myschool.dir
              + 'model/'+myschool.model_type+'.h5', 
              custom_objects={'cmetrics': cmetrics, 'hit100': hit100,})
          del self.activemodels[nr_to_replace]
        logger.info('***** Got model buffer #'+str(schoolnr)+', type: '
          + myschool.model_type)
    if test_pred:
      if (self.dbline.gpu_sim < 0) and (not self.dbline.use_websocket): 
          #Local GPU
        xdata = np.random.rand(8,self.allmodels[schoolnr]['xdim'],
          self.allmodels[schoolnr]['ydim'],3)
        self.activemodels[schoolnr].predict_on_batch(xdata)
        logger.info('***** Testrun for model #' + str(schoolnr)+', type: '
          + myschool.model_type)
      else:
        sleep(self.dbline.gpu_sim_loading / 3)
    self.modelschecked.remove(schoolnr)

  def process_buffer(self, schoolnr, logger, had_timeout=False):
    try:
      mybuffer = self.model_buffers[schoolnr]
      if schoolnr in self.myschool_cache:
        myschool= self.myschool_cache[schoolnr][0]
      else:
        myschool = school.objects.get(id=schoolnr)
        self.myschool_cache[schoolnr] = (myschool, time())

      ts_one = time()
      mybuffer.ts = time()
      slice_to_process = mybuffer.get(self.dbline.maxblock)
      framelist = slice_to_process[0]
      framesinfo = slice_to_process[1:]
      self.check_model(schoolnr, logger)
      if self.dbline.gpu_sim >= 0: #GPU Simulation with random
        if self.dbline.gpu_sim > 0:
          sleep(self.dbline.gpu_sim)
        predictions = np.empty((0, len(taglist)), np.float32)
        for i in framelist:
          myindex = round(np.sum(i).item())
          if myindex in self.cachedict:
            line = self.cachedict[myindex]
          else:
            line = []
            for j in range(len(taglist)):
              line.append(random())
            line = np.array([np.float32(line)])
            self.cachedict[myindex] = line
          predictions = np.vstack((predictions, line))
      elif self.dbline.use_websocket: #Predictions from Server
        self.ws_ts = time()
        outdict = {
          'code' : 'imgl',
          'scho' : myschool.e_school,
          'nrf' : framelist.shape[0],
        }
        self.continue_sending(json.dumps(outdict), opcode=1, logger=logger)
        while True:
          try:
            for i in range(framelist.shape[0]):
              jpgdata = cv.imencode('.jpg', framelist[i])[1].tobytes()
              schoolbytes = myschool.e_school.to_bytes(8, 'big')
              self.continue_sending(schoolbytes+jpgdata, opcode=0, logger=logger, get_answer=False)
            outdict = {
              'code' : 'done',
              'scho' : myschool.e_school,
            }
            predictions = self.continue_sending(json.dumps(outdict), opcode=1, logger=logger, get_answer=True)
            if predictions == 'incomplete':
              predictions = np.zeros((framelist.shape[0], len(taglist)), np.float32)
            else:
              predictions = np.array(json.loads(predictions), dtype=np.float32)
            break
          except (ConnectionResetError, OSError):
            sleep(djconf.getconfigfloat('long_brake', 1.0))
            self.reset_websocket()
      else: #local GPU
        if framelist.shape[0] < self.dbline.maxblock:
          patch = np.zeros((self.dbline.maxblock - framelist.shape[0], 
            framelist.shape[1], 
            framelist.shape[2], 
            framelist.shape[3]), 
            np.uint8)
          portion = np.vstack((framelist, patch))
          predictions = (
            self.activemodels[schoolnr].predict_on_batch(portion))
          predictions = predictions[:framelist.shape[0]]
        else:
          predictions = (
            self.activemodels[schoolnr].predict_on_batch(framelist))
      starting = 0
      for i in range(framelist.shape[0]):
        if ((i == framelist.shape[0] - 1) 
            or (framesinfo[0][i] != framesinfo[0][i+1])):
          if ((framesinfo[0][starting] in self.users) 
              and (framesinfo[0][starting] in self.outqueues)):
            self.outqueues[framesinfo[0][starting]].put((
              'pred_to_send', 
              predictions[starting:i+1], 
              framesinfo[0][starting:i+1],
              framesinfo[1][starting:i+1],
              framesinfo[2][starting:i+1],
            ))
          starting = i + 1
      if self.dbline.savestats > 0: #Later to be written in DB
        newtime = time()
        logtext = 'School: ' + str(schoolnr).zfill(3)
        logtext += ('  Buffer Size: ' 
          + str(len(mybuffer)).zfill(5))
        logtext += ('  Block Size: ' 
          + str(framelist.shape[0]).zfill(5))
        logtext += ('  Proc Time: ' 
          + str(round(newtime - ts_one, 3)).ljust(5, '0'))
        if had_timeout:
          logtext += ' T'
        logger.info(logtext)
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()


#***************************************************************************
#
# tf_worker client
#
#***************************************************************************

  def out_reader_proc(self, index): #called by client (c_eventer)
    while (received := self.outqueues[index].get())[0] != 'stop':
      #print('Out to queue', index, ':', received)
      if (received[0] == 'put_is_ready'):
        self.is_ready = received[1]
      elif (received[0] == 'put_xy'):
        self.xy = received[1]
      elif (received[0] == 'pred_to_send'):
        if received[4][0] == -1:
          while self.pred_out_dict[received[2][0]] is not None: 
            sleep(djconf.getconfigfloat('very_short_brake', 0.001))
          
          self.pred_out_dict[received[2][0]] = received[1]
        else:
          self.eventer.sort_in_prediction(received[4], received[3], received[1])      
      else:
        raise QueueUnknownKeyword(received[0])
    #print('Finished:', received)

  def register(self):
    self.inqueue.put(('register', ))
    self.tf_w_index = self.registerqueue.get()
    return(self.tf_w_index)

  def run_out(self, index):
    self.run_out_procs[index] = Thread(
      target=self.out_reader_proc, 
      name='RunOutThread', 
      args = (index, ))
    self.run_out_procs[index].start()
    return(self.tf_w_index)

  def unregister(self, index):
    self.inqueue.put(('unregister', index))

  def check_ready(self, index):
    if not self.is_ready:
      self.is_ready = None
      self.inqueue.put(('get_is_ready', index))
      while self.is_ready is None:
        sleep(djconf.getconfigfloat('very_short_brake', 0.001))
    return(self.is_ready)

  def get_xy(self, school, index):
    self.xy = None
    self.inqueue.put(('get_xy', school, index))
    while self.xy is None:
      sleep(self.very_short_brake)
    return(self.xy)

  def ask_pred(self, school, img_list, userindex, frame_idxs, eventnr):
    if eventnr == -1:
      self.pred_out_dict[userindex] = None
    self.inqueue.put((
      'imglist', 
      school, 
      img_list, 
      userindex, 
      frame_idxs,
      eventnr,
    ))

  def client_check_model(self, schoolnr, test_pred = False):
    self.inqueue.put((
      'checkmod', 
      schoolnr, 
      test_pred,
    ))


  def get_from_outqueue(self, userindex):
    while ((userindex not in self.pred_out_dict) 
        or (self.pred_out_dict[userindex] is None)):
      sleep(djconf.getconfigfloat('very_short_brake', 0.001))
    result = self.pred_out_dict[userindex]
    self.pred_out_dict[userindex] = None
    return(result)

  def stop_out(self, index):
    self.outqueues[index].put(('stop',))
    self.run_out_procs[index].join()

  def stop(self):
    for i in self.run_out_procs:
      if self.run_out_procs[i].is_alive():
        self.outqueues[i].put(('stop',))
        self.run_out_procs[i].join()
    self.inqueue.put(('stop',))
    self.run_process.join()
