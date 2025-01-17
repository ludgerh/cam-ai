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
import numpy as np
import cv2 as cv
import pickle
import requests
from os import environ, makedirs, path
from multiprocessing import Process, Queue
from collections import deque
from time import sleep, time
from datetime import datetime
from threading import Thread, Lock
from random import random
from traceback import format_exc
from logging import getLogger
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from inspect import currentframe, getframeinfo
from django.db import connections
from tools.l_tools import QueueUnknownKeyword, djconf, protected_db
from tools.l_sysinfo import sysinfo
from tools.c_logger import log_ini
from tools.c_redis import saferedis
from schools.c_schools import get_taglist
from .models import school as school_model, worker, school

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
      for frame in initem[0]:
        if self.websocket:
          if frame.shape[1] * frame.shape[0] > self.xdim * self.ydim:
            frame = cv.resize(frame, (self.xdim, self.ydim))
        else:
          if frame.shape[1] != self.xdim or  frame.shape[0] != self.ydim:
            frame = cv.resize(frame, (self.xdim, self.ydim))
        with self.bufferlock:
          super().append((frame, initem[1]))

  def get(self, maxcount):
    result = []
    while True:
      self.bufferlock.acquire()
      if not len(self):
        self.bufferlock.release()
        break
      else:  
        initem = self.popleft()
        self.bufferlock.release()
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
  def __init__(self, tf_w_index):
    self.nametag = 'out_dist:' + str(tf_w_index) + ':'
    self.used_adresses = set()
    
  def put(self, tf_w_index, data, timeout = None):
    while redis.exists(self.nametag + str(tf_w_index)): 
      sleep(djconf.getconfigfloat('medium_brake', 0.1))
    self.used_adresses.add(tf_w_index) 
    redis.set(self.nametag + str(tf_w_index), pickle.dumps(data)) 
    
  def get(self, tf_w_index):
    while (result := redis.get(self.nametag + str(tf_w_index))) is None: 
      sleep(djconf.getconfigfloat('medium_brake', 0.1))
    data = pickle.loads(result) 
    redis.delete(self.nametag + str(tf_w_index))
    return(pickle.loads(result))
    
  def clean_one(self, tf_w_index):
    if redis.exists(self.nametag + str(tf_w_index)):
      redis.delete(self.nametag + str(tf_w_index)) 
    
  def clean(self):
    for tf_w_index in self.used_adresses:
      self.clean_one(tf_w_index)

#***************************************************************************
#
# tf_worker common
#
#***************************************************************************

class tf_worker():

  def __init__(self, idx):
    self.id = idx
    self.dbline = worker.objects.get(id=self.id)
    #*** Requirements
    datapath = djconf.getconfig('datapath', 'data/')
    schoolsdir = djconf.getconfig('schools_dir', datapath + 'schools/')
    for schoolline in school.objects.filter(active = True, tf_worker = self.dbline):
      schooldir = schoolsdir + 'model' + str(schoolline.id) + '/'
      if not schoolline.dir:
        schoolline.dir = schooldir
        schoolline.save(update_fields=["dir"])
      makedirs(schooldir + 'model/', exist_ok=True)
      makedirs(schooldir + 'frames/', exist_ok=True)
      if self.dbline.use_litert:
        filename = schoolline.model_type + '.tflite'
        typecode = 'Q'
      else:
        filename = schoolline.model_type + '.keras'
        typecode = 'K'
      dl_path = schooldir + 'model/' + filename
      if not path.exists(dl_path):
        if self.dbline.use_litert:
          dl_url = ('https://static.cam-ai.de/models/standard/' 
            + schoolline.model_type 
            + '/litert/efficientnetv2-b0.tflite')
        else:
          dl_url = ('https://static.cam-ai.de/models/standard/' 
            + schoolline.model_type 
            + '/keras/efficientnetv2-b0.keras')
        r = requests.get(dl_url, allow_redirects=True)
        open(dl_path, 'wb').write(r.content)
    #*** Common Vars

    self.inqueue = Queue()
    self.registerqueue = Queue()
    self.my_output = output_dist(self.id)  
    self.is_ready = False

    #*** Server Var
    self.check_ts = time()
    self.models = {}
    self.active_models = 0

    #*** Client Var
    self.run_out_procs = {}
    self.pred_out_dict = {}
    self.pred_out_lock = Lock()
    self.model_check_lock = Lock()
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
    from websocket._exceptions import (WebSocketTimeoutException, 
      WebSocketConnectionClosedException,
      WebSocketBadStatusException, 
      WebSocketAddressException,
    )
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
        self.ws.recv()    
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
              #AttributeError,
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
        #print('TFW in', received[:2])
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
          self.check_model(received[1], self.logger, True)
          while not 'xdim' in self.models[received[1]]:
            sleep(djconf.getconfigfloat('long_brake', 1.0))
          xdim = self.models[received[1]]['xdim']
          ydim = self.models[received[1]]['ydim']
          self.my_output.put(received[2], ('put_xy', (xdim, ydim)))
        elif (received[0] == 'imglist'):
          schoolnr = received[1]
          self.check_model(schoolnr, self.logger, True)
          while not 'xdim' in self.models[schoolnr]:
            sleep(djconf.getconfigfloat('long_brake', 1.0))
          if schoolnr not in self.model_buffers:
            self.model_buffers[schoolnr] = model_buffer(schoolnr, 
              self.models[schoolnr]['xdim'], 
              self.models[schoolnr]['ydim'],
              self.dbline.use_websocket,
            )
          self.model_buffers[schoolnr].pause = False
          self.model_buffers[schoolnr].append(received[2:])
        elif (received[0] == 'register'):
          myuser = tf_user()
          self.users[myuser.id] = myuser
          self.registerqueue.put(myuser.id)
        elif (received[0] == 'checkmod'):
          self.check_model(received[1], self.logger, True)
        else:
          raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error('Error in process: ' + self.logname + ' (in_queue_handler)')
      self.logger.error(format_exc())

  def runner(self):
    try:
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
      self.model_buffers = None
      self.load_model = None
      if self.dbline.gpu_sim >= 0: # Random values
        self.cachedict = {}
      elif self.dbline.use_websocket: # Websocket
        if self.dbline.wsname:
          self.reset_websocket()
      else: #Local CPU or GPU
        if self.dbline.use_litert:
          if sysinfo()['hw'] == 'raspi':
            from tflite_runtime import interpreter as tflite
          else:
            from tensorflow import lite as tflite
          self.logger.info("*** Using LiteRT ***")
          self.tflite = tflite
        else:
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
      self.is_ready = True
      schoolnr = -1
      while (self.do_run 
          and (self.model_buffers is None
          or len(self.model_buffers) == 0)):
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
              timeout = time() > self.model_buffers[schoolnr].ts + self.dbline.timeout
              if (schoolnr in self.model_buffers
                  and (len(self.model_buffers[schoolnr]) >= self.dbline.maxblock
                  or timeout)):
                if self.do_run and len(self.model_buffers[schoolnr]):
                  self.process_buffer(schoolnr, self.logger, timeout)
                self.model_buffers[schoolnr].ts = time() 
              else:
                sleep(djconf.getconfigfloat('medium_brake', 0.1))
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())

  def run(self):
    self.do_run = True
    self.run_process = Process(target=self.runner)
    connections.close_all()
    self.run_process.start()  

  def check_model(self, schoolnr, logger, test_pred = False):
    if schoolnr not in self.models:
      self.models[schoolnr] = {}
      #self.models[schoolnr]['dbline'] = school_model.objects.get(id = schoolnr)
      self.models[schoolnr]['dbline'] = protected_db(
        school_model.objects.get, kwargs = {'id' : schoolnr, }
      )
      self.models[schoolnr]['model_type'] = None
    school_dbline = self.models[schoolnr]['dbline']
    self.models[schoolnr]['last_check'] = time()
    if self.check_ts + 60.0 < time() and self.models[schoolnr]['model_type'] is not None:
      protected_db(self.models[schoolnr]['dbline'].refresh_from_db)
      if (school_dbline.lastmodelfile is not None
          and	(datetime.timestamp(school_dbline.lastmodelfile) > self.models[schoolnr]['time']
          or school_dbline.model_type != self.models[schoolnr]['model_type']
          )):
        if schoolnr in self.model_buffers:  
          self.model_buffers[schoolnr].pause = True 
        self.models[schoolnr]['model_type'] = None   
        del self.models[schoolnr]['model']
        self.active_models -= 1
      self.check_ts = time()
    if self.models[schoolnr]['model_type'] is None: 
      if self.active_models >= self.dbline.max_nr_models:
        nr_to_replace = min(self.models, key= lambda x: self.models[x]['last_check'])	
        self.models[nr_to_replace]['model_type'] = None   
        del self.models[nr_to_replace]['model']
        self.active_models -= 1
      if (self.dbline.gpu_sim >= 0) or self.dbline.use_websocket: #remote or simulation
        self.models[schoolnr]['time'] = time()
        self.models[schoolnr]['model_type'] = 'simulation'
      else:  #lokal GPU
        self.models[schoolnr]['time'] = datetime.timestamp(school_dbline.lastmodelfile)
        self.models[schoolnr]['model_type'] = school_dbline.model_type
        sleep(self.dbline.gpu_sim_loading)
      if self.dbline.gpu_sim >= 0:
        self.models[schoolnr]['xdim'] = 50
        self.models[schoolnr]['ydim'] = 50
      elif self.dbline.use_websocket:
        outdict = {
          'code' : 'get_xy',
          'scho' : school_dbline.e_school,
        }
        xytemp = json.loads(self.continue_sending(json.dumps(outdict), 
          opcode=1, logger=logger, get_answer=True))
        self.models[schoolnr]['xdim'] = xytemp[0]
        self.models[schoolnr]['ydim'] = xytemp[1]
        sleep(self.dbline.gpu_sim_loading) 
      else: #lokal GPU
        if self.dbline.use_litert:
          model_path = (school_dbline.dir 
            + 'model/' + school_dbline.model_type + '.tflite')
        else:
          model_path = (school_dbline.dir
            + 'model/' + school_dbline.model_type + '.keras')
        logger.info('***** Loading model file #'+str(schoolnr)
          + ', file: '+model_path)
        self.models[schoolnr]['path'] = model_path  
        self.models[schoolnr]['model_type'] = school_dbline.model_type
        if self.dbline.use_litert:
          interpreter = self.tflite.Interpreter(model_path = model_path, num_threads = 2)
          interpreter.allocate_tensors()
          self.models[schoolnr]['model'] = interpreter
          self.models[schoolnr]['int_input'] = interpreter.tensor(interpreter.get_input_details()[0]["index"])
          self.models[schoolnr]['int_output'] = interpreter.tensor(interpreter.get_output_details()[0]["index"])
          self.models[schoolnr]['xdim'] = interpreter.get_input_details()[0]['shape_signature'][2]
          self.models[schoolnr]['ydim'] = interpreter.get_input_details()[0]['shape_signature'][1]
        else: 
          while self.load_model is None:
            sleep(djconf.getconfigfloat('long_brake', 1.0))
          loaded_model = self.load_model(model_path)
          self.models[schoolnr]['model'] = loaded_model
          self.models[schoolnr]['xdim'] = loaded_model.layers[0].input_shape[2]
          self.models[schoolnr]['ydim'] = loaded_model.layers[0].input_shape[1]
        logger.info('***** Got model file #'+str(schoolnr) 
          + ', file: '+model_path)
      if test_pred:
        xdata = np.random.rand(8,self.models[schoolnr]['xdim'],
          self.models[schoolnr]['ydim'],3)
        if self.dbline.use_litert: 
          logger.info(str(self.models[schoolnr]['model'].get_input_details()[0]))
          self.models[schoolnr]['int_input']().fill(128)
          self.models[schoolnr]['model'].invoke()

        else:
          self.models[schoolnr]['model'].predict_on_batch(xdata)
        logger.info('***** Testrun for model #' + str(schoolnr)+', type: '
          + self.models[schoolnr]['model_type'])
      self.active_models += 1

  def process_buffer(self, schoolnr, logger, had_timeout=False):
    mybuffer = self.model_buffers[schoolnr]
    ts_one = time()
    slice_to_process = mybuffer.get(self.dbline.maxblock)
    framelist = [item[0] for item in slice_to_process]
    framesinfo = [item[1] for item in slice_to_process]
    self.check_model(schoolnr, logger, True)
    self.model_buffers[schoolnr].pause = False
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
        'scho' : models[schoolnr]['dbline'].e_school,
      }
      result = json.loads(
          self.continue_sending(json.dumps(outdict), 
          opcode=1, 
          logger=logger, get_answer=True
        )
      )
      if result != 'OK':
        logger.error(result)
        return()
      while True:
        try:
          for item in framelist:
            jpgdata = cv.imencode('.jpg', item)[1].tobytes()
            schoolbytes = models[schoolnr]['dbline'].e_school.to_bytes(8, 'big')
            self.continue_sending(schoolbytes+jpgdata, opcode=0, 
              logger=logger, get_answer=False)
          outdict = {
            'code' : 'done',
            'scho' : models[schoolnr]['dbline'].e_school,
          }
          predictions = self.continue_sending(json.dumps(outdict), opcode=1, 
            logger=logger, get_answer=True)
          try:  
            predictions = json.loads(predictions) 
          except json.decoder.JSONDecodeError:
            self.logger.error('Error in process: ' + self.logname)
            self.logger.error(format_exc())
            self.logger.error('***** Received predictions: *' + str(predictions) + '*')
            predictions = None  
          if predictions is None:
            predictions = np.zeros((len(framelist), len(taglist)), np.float32)
          else:
            predictions = np.array(predictions, dtype=np.float32)
          break
        except (ConnectionResetError, OSError):
          sleep(djconf.getconfigfloat('long_brake', 1.0))
          self.reset_websocket()
    else: #local GPU
      if self.dbline.use_litert: #Predictions Tensorflow Lite
        predictions = np.empty((0, len(taglist)), np.float32)
        for item in framelist:
          np.copyto(self.models[schoolnr]['int_input'](), item)
          self.models[schoolnr]['model'].invoke()
          line=np.zeros((1, len(taglist)), np.float32)
          np.copyto(line, self.models[schoolnr]['int_output']())
          predictions = np.vstack((predictions, line))
      else:
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
        if frames_ok:    
          npframelist = np.vstack(npframelist)
          self.check_model(schoolnr, logger, True)
          self.models[schoolnr]['model'].summary
          predictions = (
            self.models[schoolnr]['model'].predict_on_batch(npframelist))
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
            ), timeout=5.0)
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

#***************************************************************************
#
# tf_worker client
#
#***************************************************************************

  def out_reader_proc(self, index): #called by client (c_eventer)
    try:
      while (received := self.my_output.get(index))[0] != 'stop':
        if (received[0] == 'put_is_ready'):
          self.is_ready = received[1]
        elif (received[0] == 'put_xy'):
          self.xy = received[1]
        elif (received[0] == 'pred_to_send'):
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
              sleep(djconf.getconfigfloat('very_short_brake', 0.01))
              #break
        else:
          raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error('Error in process: ' + self.logname + ' (out_reader_proc)')
      self.logger.error(format_exc())

  def register(self):
    self.inqueue.put(('register', ))
    self.tf_w_index = self.registerqueue.get()
    self.my_output.clean_one(self.tf_w_index)
    #print('*** Register', self.tf_w_index)
    return(self.tf_w_index)

  def run_out(self, index):
    self.run_out_procs[index] = Thread(
      target=self.out_reader_proc, 
      name='RunOutThread', 
      args = (index, ))
    self.run_out_procs[index].start()
    return(self.tf_w_index)

  def unregister(self, index):
    #print('*** Unregister', index)
    self.inqueue.put(('unregister', index))

  def check_ready(self, index):
    if not self.is_ready:
      self.is_ready = None
      self.inqueue.put(('get_is_ready', index))
      while self.is_ready is None:
        sleep(djconf.getconfigfloat('very_short_brake', 0.01))
    return(self.is_ready)

  def get_xy(self, school, index):
    self.xy = None
    self.inqueue.put(('get_xy', school, index))
    while self.xy is None:
      sleep(self.very_short_brake)
    return(self.xy)

  def ask_pred(self, school, img_list, userindex):
    with  self.pred_out_lock:
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

  def outqueue_empty(self, userindex):
    with self.pred_out_lock:
      result = ((userindex not in self.pred_out_dict) 
        or (self.pred_out_dict[userindex] is None))
    return(result)

  def get_from_outqueue(self, userindex):
    while True:
      self.pred_out_lock.acquire()
      if ((userindex not in self.pred_out_dict) 
          or self.pred_out_dict[userindex] is None):
        self.pred_out_lock.release()
        sleep(djconf.getconfigfloat('medium_brake', 0.1))
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
