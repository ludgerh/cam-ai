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
import numpy as np
import cv2 as cv
import sys
import gc
import pickle
from os import environ, path, makedirs
from multiprocessing import Process, Queue
from collections import deque
from time import sleep, time
from threading import Thread, Lock, get_native_id
from random import random
from multitimer import MultiTimer
from traceback import format_exc
from logging import getLogger
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from inspect import currentframe, getframeinfo, stack
from websocket._exceptions import (WebSocketTimeoutException, 
  WebSocketConnectionClosedException,
  WebSocketBadStatusException, 
  WebSocketAddressException,
)
from django.db.utils import OperationalError
from django.db import connections, connection
from tools.l_tools import QueueUnknownKeyword, djconf, get_proc_name
if djconf.getconfigbool('local_trainer', False):
  from plugins.train_worker_gpu.train_gpu_tools import cmetrics, hit100
from tools.c_logger import log_ini
from tools.c_redis import saferedis
from .models import school, worker
from schools.c_schools import get_taglist

from psutil import virtual_memory
from tools.l_tools import displaybytes

tf_workers = {}
taglist = get_taglist(1)
redis = saferedis()

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

  def __init__(self, schoolnr, xdim, ydim, websocket):
    super().__init__()
    self.ts = time()
    self.xdim = xdim
    self.ydim = ydim
    self.bufferlock = Lock()
    self.websocket = websocket
    self.pause = True

  def append(self, initem):
    # structure of initem:
    # initem[0] = np.imagelist, initem[1] = userindex
    # structure of outitem:
    # outitem[0] = np.image, outitem[1] = userindex
    if self.pause:
      ('short_brake', 0.01)
    else:  
      with self.bufferlock:
        for frame in initem[0]:
          if self.websocket:
            if ((frame.shape[1] * frame.shape[0]) > (self.xdim * self.ydim)):
              frame = cv.resize(frame, (self.xdim, self.ydim))
          else:
            frame = cv.resize(frame, (self.xdim, self.ydim))
          super().append((frame, initem[1]))

  def get(self, maxcount):
    result = []
    while True:
      with self.bufferlock:
        if not len(self):
          break
        initem = self.popleft()
      result.append(initem)
      if len(result) >= maxcount:
        break 
    return(result)

class tf_user(object):
  clientset = set()
  clientlock = Lock()

  def __init__(self):
    with self.clientlock:
      i = 0
      while (i in self.clientset):
        i += 1
      self.clientset.add(i)
      self.id = i 

  def __del__(self):
    with self.clientlock:
      self.clientset.discard(self.id)
      
class output_dist():   
  def __init__(self, worker_nr):
    self.nametag = 'out_dist:' + str(worker_nr) + ':'
    self.used_adresses = set()
    
  def put(self, address, data):
    while redis.exists(self.nametag + str(address)):      
      sleep(djconf.getconfigfloat('short_brake', 0.01))
    self.used_adresses.add(address) 
    redis.set(self.nametag + str(address), pickle.dumps(data))   
    
  def get(self, address):
    while (result := redis.get(self.nametag + str(address))) is None: 
      sleep(djconf.getconfigfloat('short_brake', 0.01))
    redis.delete(self.nametag + str(address))
    return(pickle.loads(result))
    
  def clean(self):
    for address in self.used_adresses:
      if redis.exists(self.nametag + str(address)):
        redis.delete(self.nametag + str(address))  

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

    self.inqueue = Queue()
    self.registerqueue = Queue()
    self.my_output = output_dist(self.id)  
    self.is_ready = False

    #*** Server Var
    self.myschool_cache = {}
    self.allmodels = {}
    self.activemodels = {}
    self.modelschecked = set()

    #*** Client Var
    self.run_out_procs = {}
    self.pred_out_dict = {}
    self.pred_out_lock = Lock()
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
          'ws_id' : self.dbline.wsid,
          'ws_name' : self.dbline.wsname,
          'worker_nr' : self.id,
          'soft_ver' : djconf.getconfig('version', 'not set'),
        }
        self.ws.send(json.dumps(outdict), opcode=1) #1 = Text
        break
      except (BrokenPipeError, 
            TimeoutError,
            WebSocketBadStatusException, 
            ConnectionRefusedError,
            WebSocketConnectionClosedException,
            WebSocketAddressException,
            OSError,
          ):
        self.logger.warning('BrokenPipe or Timeout while resetting '
          + 'prediction websocket server')
        sleep(djconf.getconfigfloat('long_brake', 1.0))

  def continue_sending(self, payload, opcode=1, logger=None, get_answer=False):
    while self.do_run:
      while self.do_run:
        try:
          if opcode:
            self.ws.send(payload, opcode = 1) # 1 = Text
            frameinfo = getframeinfo(currentframe())
          else:
            self.ws.send_binary(payload) # 0 = Bytes
            frameinfo = getframeinfo(currentframe())
          break
        except (BrokenPipeError,
              TimeoutError,
              WebSocketBadStatusException, 
              ConnectionRefusedError,
              WebSocketConnectionClosedException,
              WebSocketAddressException,
              OSError,
            ):
          if logger:
            frameinfo = getframeinfo(currentframe())
            logger.warning('Pipe error while sending in ' + frameinfo.filename 
              + ':' + str(frameinfo.lineno))
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
            logger.warning('Pipe error while reading in ' + frameinfo.filename 
              + ':' + str(frameinfo.lineno))
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
          self.my_output.clean()
          break
        elif (received[0] == 'unregister'):
          if received[1] in self.users:
            del self.users[received[1]]
        elif (received[0] == 'get_is_ready'):
          self.my_output.put(received[1], ('put_is_ready', self.is_ready))
        elif (received[0] == 'get_xy'):
          self.check_allmodels(received[1], self.logger)
          xdim = self.allmodels[received[1]]['xdim']
          ydim = self.allmodels[received[1]]['ydim']
          self.my_output.put(received[2], ('put_xy', (xdim, ydim)))
        elif (received[0] == 'imglist'):
          schoolnr = received[1]
          if schoolnr not in self.model_buffers:
            self.check_allmodels(schoolnr, self.logger)
            while not 'xdim' in self.allmodels[schoolnr]:
              sleep(djconf.getconfigfloat('long_brake', 1.0))
            self.model_buffers[schoolnr] = model_buffer(schoolnr, 
              self.allmodels[schoolnr]['xdim'], 
              self.allmodels[schoolnr]['ydim'],
              self.dbline.use_websocket,
            )
            self.model_buffers[schoolnr].pause = False
          self.model_buffers[schoolnr].append(received[2:])
        elif (received[0] == 'register'):
          myuser = tf_user()
          self.users[myuser.id] = myuser
          self.registerqueue.put(myuser.id)
        elif (received[0] == 'checkmod'):
          self.check_allmodels(received[1], self.logger)
        else:
          raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def runner(self):
    self.dbline = worker.objects.get(id=self.id)
    self.users = {}
    Thread(target=self.in_queue_thread, name='TFW_InQueueThread').start()
    signal(SIGINT, sigint_handler)
    signal(SIGTERM, sigint_handler)
    signal(SIGHUP, sigint_handler)
    self.logname = 'tf_worker #'+str(self.dbline.id)
    self.logger = getLogger(self.logname)
    log_ini(self.logger, self.logname)
    setproctitle('CAM-AI-TFWorker #'+str(self.dbline.id))
    if (self.dbline.gpu_sim < 0) and (not self.dbline.use_websocket): #Local CPU or GPU
      environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
      if self.dbline.gpu_nr == -1:
        environ["CUDA_VISIBLE_DEVICES"] = ''
      else:  
        environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.gpu_nr)
      import tensorflow as tf 
      self.logger.info("TensorFlow version: "+tf.__version__)
      cpus = tf.config.list_physical_devices('CPU')
      self.logger.info('+++++ tf_worker CPUs: '+str(cpus))
      gpus = tf.config.list_physical_devices('GPU')
      self.logger.info('+++++ tf_worker GPUs: '+str(gpus))
      if self.dbline.gpu_nr == -1:
        self.cuda_select = '/CPU:0'
      else:  
        self.cuda_select = '/GPU:'+str(self.dbline.gpu_nr)
        for gpu in gpus:
          tf.config.experimental.set_memory_growth(gpu, True)
      self.logger.info('+++++ tf_worker Selected: '+self.cuda_select)
      from tensorflow.keras.models import load_model
      self.tf = tf
      self.load_model = load_model
    self.model_buffers = {}
    if self.dbline.gpu_sim >= 0:
      self.cachedict = {}
    elif self.dbline.use_websocket:
      if self.dbline.wsname:
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
        if self.model_buffers:
          schoolnr += 1
          if schoolnr > max(self.model_buffers):
            schoolnr = 0
          if schoolnr in self.model_buffers:
            break
        else:
          schoolnr = -1 
          break  
      if self.do_run:
        if schoolnr > -1:
          if self.model_buffers[schoolnr].pause:
            sleep(djconf.getconfigfloat('long_brake', 1.0)) 
          else:   
            new_time = time()
            if (schoolnr in self.model_buffers
                and (len(self.model_buffers[schoolnr]) >= self.dbline.maxblock
                or new_time > self.model_buffers[schoolnr].ts + self.dbline.timeout)):
              self.model_buffers[schoolnr].ts = new_time  
              while self.do_run and len(self.model_buffers[schoolnr]):
                self.process_buffer(schoolnr, self.logger)
            else:
              sleep(djconf.getconfigfloat('short_brake', 0.01))
    self.finished = True
    self.logger.info('Finished Process '+self.logname+'...')
    self.logger.handlers.clear()

  def run(self):
    self.do_run = True
    self.run_process = Process(target=self.runner)
    connections.close_all()
    self.run_process.start()
    
  def check_allmodels(self, schoolnr, logger):
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
            or (myschool.lastmodelfile > self.allmodels[schoolnr]['time'])
            or (myschool.model_type != self.allmodels[schoolnr]['model_type'])
            )):
          self.model_buffers[schoolnr].pause = True  
          del self.allmodels[schoolnr]
          if schoolnr in self.activemodels:
            del self.activemodels[schoolnr]
          if schoolnr in self.model_buffers:
            del self.model_buffers[schoolnr]
      model_path = myschool.dir+'model/'+myschool.model_type+'.h5'
    if not (schoolnr in self.allmodels):
      self.allmodels[schoolnr] = {}
      if (self.dbline.gpu_sim >= 0) or self.dbline.use_websocket: #remote or simulation
        self.allmodels[schoolnr]['time'] = time()
        self.allmodels[schoolnr]['model_type'] = 'simulation'
      else:  #lokal GPU
        self.allmodels[schoolnr]['time'] = myschool.lastmodelfile
        self.allmodels[schoolnr]['model_type'] = myschool.model_type
      if self.dbline.gpu_sim >= 0:
        self.allmodels[schoolnr]['xdim'] = 50
        self.allmodels[schoolnr]['ydim'] = 50
        sleep(self.dbline.gpu_sim_loading)
      elif self.dbline.use_websocket:
        myschool = school.objects.get(id=schoolnr)
        outdict = {
          'code' : 'get_xy',
          'scho' : myschool.e_school,
        }
        xytemp = json.loads(self.continue_sending(json.dumps(outdict), 
          opcode=1, logger=logger, get_answer=True))
        self.allmodels[schoolnr]['xdim'] = xytemp[0]
        self.allmodels[schoolnr]['ydim'] = xytemp[1]
        sleep(self.dbline.gpu_sim_loading) 
      else: #lokal GPU
        try:
          logger.info('***** Loading model file #'+str(schoolnr)
            + ', file: '+model_path)
          tempmodel = self.load_model(
            model_path, 
            custom_objects={'cmetrics': cmetrics, 'hit100': hit100,})
          self.allmodels[schoolnr]['path'] = model_path  
          self.allmodels[schoolnr]['type'] = myschool.model_type
          self.allmodels[schoolnr]['weights'] = []
          self.allmodels[schoolnr]['weights'].append(
            tempmodel.get_layer(name=myschool.model_type).get_weights())
          self.allmodels[schoolnr]['weights'].append(
            tempmodel.get_layer(name='CAM-AI_Dense1').get_weights())
          self.allmodels[schoolnr]['weights'].append(
            tempmodel.get_layer(name='CAM-AI_Dense2').get_weights())
          self.allmodels[schoolnr]['weights'].append(
            tempmodel.get_layer(name='CAM-AI_Dense3').get_weights())
          self.allmodels[schoolnr]['ydim'] = tempmodel.layers[0].input_shape[2]
          self.allmodels[schoolnr]['xdim'] = tempmodel.layers[0].input_shape[1]
          logger.info('***** Got model file #'+str(schoolnr) 
            + ', file: '+model_path)
        except:
          self.logger.error(format_exc())
          self.logger.handlers.clear()
    self.modelschecked.remove(schoolnr)

  def check_activemodels(self, schoolnr, logger, test_pred = False):
    if schoolnr in self.modelschecked:
      return()
    self.modelschecked.add(schoolnr)  
    if not (schoolnr in self.activemodels):
      logger.info('***** Loading model buffer #'+str(schoolnr)+', file: '
        + self.allmodels[schoolnr]['path'])
      if len(self.activemodels) < self.dbline.max_nr_models:
        tempmodel = self.load_model(
          self.allmodels[schoolnr]['path'], 
          custom_objects={'cmetrics': cmetrics, 'hit100': hit100,})
        self.activemodels[schoolnr] = {}
        self.activemodels[schoolnr]['model'] = tempmodel
        self.activemodels[schoolnr]['type'] = self.allmodels[schoolnr]['type']
        self.activemodels[schoolnr]['xdim'] = self.allmodels[schoolnr]['xdim']
        self.activemodels[schoolnr]['ydim'] = self.allmodels[schoolnr]['ydim']
        self.activemodels[schoolnr]['time'] = time()
      else: #if # of models > self.dbline.max_nr_models
        nr_to_replace = min(self.activemodels, 
          key= lambda x: self.activemodels[x]['time'])	
        self.activemodels[schoolnr] = self.activemodels[nr_to_replace]
        self.activemodels[schoolnr]['type'] = self.allmodels[schoolnr]['type']
        self.activemodels[schoolnr]['xdim'] = self.allmodels[schoolnr]['xdim']
        self.activemodels[schoolnr]['ydim'] = self.allmodels[schoolnr]['ydim']
        self.activemodels[schoolnr]['time'] = time()
        self.activemodels[schoolnr]['model'].get_layer(name=self.activemodels[schoolnr]['type']).set_weights(
          self.allmodels[schoolnr]['weights'][0])
        self.activemodels[schoolnr]['model'].get_layer(name='CAM-AI_Dense1').set_weights(
          self.allmodels[schoolnr]['weights'][1])
        self.activemodels[schoolnr]['model'].get_layer(name='CAM-AI_Dense2').set_weights(
          self.allmodels[schoolnr]['weights'][2])
        self.activemodels[schoolnr]['model'].get_layer(name='CAM-AI_Dense3').set_weights(
          self.allmodels[schoolnr]['weights'][3])
        del self.activemodels[nr_to_replace]
      logger.info('***** Got model buffer #'+str(schoolnr)+', file: '
        + self.allmodels[schoolnr]['path'])
      if test_pred:
        xdata = np.random.rand(8,self.allmodels[schoolnr]['xdim'],
          self.allmodels[schoolnr]['ydim'],3)
        self.activemodels[schoolnr]['model'].predict_on_batch(xdata)
        logger.info('***** Testrun for model #' + str(schoolnr)+', type: '
          + self.allmodels[schoolnr]['type'])
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
      slice_to_process = mybuffer.get(self.dbline.maxblock)
      framelist = [item[0] for item in slice_to_process]
      framesinfo = [item[1] for item in slice_to_process]
      self.check_allmodels(schoolnr, logger)
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
        }
        self.continue_sending(json.dumps(outdict), opcode=1, logger=logger)
        while True:
          try:
            for item in framelist:
              jpgdata = cv.imencode('.jpg', item)[1].tobytes()
              schoolbytes = myschool.e_school.to_bytes(8, 'big')
              self.continue_sending(schoolbytes+jpgdata, opcode=0, 
                logger=logger, get_answer=False)
            outdict = {
              'code' : 'done',
              'scho' : myschool.e_school,
            }
            predictions = self.continue_sending(json.dumps(outdict), opcode=1, 
              logger=logger, get_answer=True)
            predictions = json.loads(predictions) 
            if predictions is None:
              predictions = np.zeros((len(framelist), len(taglist)), np.float32)
            else:
              predictions = np.array(predictions, dtype=np.float32)
            break
          except (ConnectionResetError, OSError):
            sleep(djconf.getconfigfloat('long_brake', 1.0))
            self.reset_websocket()
      else: #local GPU
        frames_ok = True
        try:
          npframelist = []
          for item in framelist:
            if item is not None and len(item.shape) == 3:
              npframelist.append(np.expand_dims(item, axis=0))
            else:
              frames_ok = False  
              break
        except:
          frame_ok = False
          logger.error(format_exc())
          logger.handlers.clear()      
        if frames_ok:    
          npframelist = np.vstack(npframelist)
          self.check_activemodels(schoolnr, logger)
          self.activemodels[schoolnr]['model'].summary
          predictions = (
            self.activemodels[schoolnr]['model'].predict_on_batch(npframelist))
        else:
          logger.warning('Defective image in c_tfworkers / processbuffer') 
          predictions = None    
      if predictions is not None:
        starting = 0
        for i in range(len(framelist)):
          if ((i == len(framelist) - 1) 
              or (framesinfo[i] != framesinfo[i+1])):
            if (framesinfo[starting] in self.users):
              self.my_output.put(framesinfo[starting], (
                'pred_to_send', 
                predictions[starting:i+1], 
                framesinfo[starting],
              ))
            starting = i + 1
        if self.dbline.savestats > 0: #Later to be written in DB
          newtime = time()
          logtext = 'School: ' + str(schoolnr).zfill(3)
          logtext += ('  Buffer Size: ' 
            + str(len(mybuffer)).zfill(5))
          logtext += ('  Block Size: ' 
            + str(len(framelist)).zfill(5))
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
    while (received := self.my_output.get(index))[0] != 'stop':
      #print('Out to queue', index, ':', received)
      if (received[0] == 'put_is_ready'):
        self.is_ready = received[1]
      elif (received[0] == 'put_xy'):
        self.xy = received[1]
      elif (received[0] == 'pred_to_send'):
        #print('Out to queue', index, ':', received)
        while True:
          self.pred_out_lock.acquire()
          if  received[2] not in self.pred_out_dict:
            self.pred_out_dict[received[2]] = None
          if self.pred_out_dict[received[2]] is None:
            self.pred_out_dict[received[2]] = received[1]
            self.pred_out_lock.release()
            break
          else: 
            self.pred_out_lock.release() 
            sleep(djconf.getconfigfloat('very_short_brake', 0.001))
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

  def ask_pred(self, school, img_list, userindex):
    with  self.pred_out_lock:
      #self.pred_out_dict[userindex] = None
      self.inqueue.put((
        'imglist', 
        school, 
        img_list, 
        userindex, 
      ))

  def client_check_model(self, schoolnr, test_pred = False):
    self.inqueue.put((
      'checkmod', 
      schoolnr, 
      test_pred,
    ))


  def get_from_outqueue(self, userindex):
    while True:
      self.pred_out_lock.acquire()
      if ((userindex not in self.pred_out_dict) 
          or (self.pred_out_dict[userindex] is None)):
        self.pred_out_lock.release()
        sleep(djconf.getconfigfloat('very_short_brake', 0.01))
      else:  
        result = self.pred_out_dict[userindex]
        self.pred_out_dict[userindex] = None
        self.pred_out_lock.release()
        break
    return(result)

  def stop_out(self, index):
    self.my_output.put(index, ('stop',))
    self.run_out_procs[index].join()

  def stop(self):
    for i in self.run_out_procs:
      if self.run_out_procs[i].is_alive():
        self.my_output.put(i, ('stop',))
        self.run_out_procs[i].join()
    self.inqueue.put(('stop',))
    self.run_process.join()
