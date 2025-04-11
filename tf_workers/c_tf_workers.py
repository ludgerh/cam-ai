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
v1.6.1 30.03.2025
"""

import os
import numpy as np
import cv2 as cv
import pickle
import asyncio
import aiofiles
from multiprocessing import Queue as p_queue, SimpleQueue as s_queue
from collections import deque
from time import time
from datetime import datetime
from threading import Thread, Lock as t_lock
from random import random
from logging import getLogger
from signal import signal, SIGINT
from setproctitle import setproctitle
from tools.l_sysinfo import sysinfo
from tools.l_break import (a_break_time, a_break_type, break_type, a_break_auto, 
  BR_SHORT, BR_MEDIUM, BR_LONG, )
from tools.c_redis import my_redis as safe_redis

#***************************************************************************
#
# tools common
#
#***************************************************************************

def sigint_handler(signal, frame):
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
    self.bufferlock = t_lock()
    self.websocket = websocket
    self.pause = True

  def append(self, initem):
    # structure of initem:
    # initem[0] = userindex, schoolnr, initem[1] = np.image, initem[2] = np.image...
    # structure of outitem:
    # outitem[0] = np.image, outitem[1] = userindex
    if self.pause:
      break_type(BR_LONG)
      return()
    for frame in initem[2:]:
      if self.websocket:
        if frame.shape[1] * frame.shape[0] > self.xdim * self.ydim:
          frame = cv.resize(frame, (self.xdim, self.ydim))
      else:
        if frame.shape[1] != self.xdim or  frame.shape[0] != self.ydim:
          frame = cv.resize(frame, (self.xdim, self.ydim))
      with self.bufferlock:
        super().append((frame, initem[0]))

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
  clientlock = t_lock()

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
  def __init__(self, idx):
    self.nametag = 'cam-ai.tf_worker.output:' + str(idx) + ':'
    self.used_adresses = set()
    self.auto_break = a_break_auto(tmin = 0.01, tmax = 0.1, rate = 0.01)
    
  async def put(self, tf_w_index, data):
    while safe_redis.exists(self.nametag + str(tf_w_index) + ':'): 
      await self.auto_break.wait()
    self.auto_break.reset()
    self.used_adresses.add(tf_w_index) 
    safe_redis.set(self.nametag + str(tf_w_index) + ':', pickle.dumps(data)) 
    
  async def get(self, tf_w_index):
    while (result := safe_redis.get(self.nametag + str(tf_w_index) + ':')) is None:
      await self.auto_break.wait()
    self.auto_break.reset()
    data = pickle.loads(result) 
    safe_redis.delete(self.nametag + str(tf_w_index) + ':')
    return(pickle.loads(result))
    
  def clean_one(self, tf_w_index):
    if safe_redis.exists(self.nametag + str(tf_w_index) + ':'):
      safe_redis.delete(self.nametag + str(tf_w_index) + ':') 
    
  def clean(self):
    for tf_w_index in self.used_adresses:
      self.clean_one(tf_w_index)

#***************************************************************************
#
# tf_worker common
#
#***************************************************************************

from tools.c_spawn import spawn_process

class tf_worker(spawn_process):
  def __init__(self, idx, ):
    self.id = idx
    self.registerqueue = s_queue()
    super().__init__(buffer_code = 'OOON')
    
  async def process_received(self, received):  
    result = True
    #print('§§§§§ Server-Inqueue', received)
    if (received[0] == 'unregister'):
      if received[1] in self.users:
        del self.users[received[1]]
    elif (received[0] == 'get_is_ready'):
      await self.my_output.put(received[1], ('put_is_ready', self.is_ready))
    elif (received[0] == 'get_xy'):
      await self.check_model(received[2], self.logger, True)
      while not 'xdim' in self.models[received[2]]:
        await a_break_type(BR_LONG)
      xdim = self.models[received[2]]['xdim']
      ydim = self.models[received[2]]['ydim']
      await self.my_output.put(received[1], ('put_xy', (xdim, ydim)))
    elif (received[0] == 'ask_pred'):
      schoolnr = received[2]
      await self.check_model(schoolnr, self.logger, True)
      while not 'xdim' in self.models[schoolnr]:
        await a_break_type(BR_LONG)
      if schoolnr not in self.model_buffers:
        self.model_buffers[schoolnr] = model_buffer(schoolnr, 
          self.models[schoolnr]['xdim'], 
          self.models[schoolnr]['ydim'],
          self.dbline.use_websocket,
        )
      self.model_buffers[schoolnr].pause = False
      self.model_buffers[schoolnr].append(received[1:])
    elif (received[0] == 'register'):
      myuser = tf_user()
      self.users[myuser.id] = myuser
      self.registerqueue.put(myuser.id)
    elif (received[0] == 'checkmod'):
      await self.check_model(received[2], self.logger, True)
    else:
      result = False  
    return(result)

  async def async_runner(self):
    try: 
      import django
      django.setup()
      from tools.c_logger import alog_ini
      from tools.l_break import a_break_time, a_break_type, BR_LONG
      from tools.l_tools import djconf
      from schools.c_schools import get_taglist
      from .models import worker as dbworker, school as dbschool
      self.dbschool = dbschool
      self.dbline = await dbworker.objects.aget(id = self.id)
      setproctitle('CAM-AI-TFWorker #'+str(self.dbline.id))
      #*** Requirements
      self.my_output = output_dist(self.id)
      datapath = await djconf.agetconfig('datapath', 'data/')
      schoolsdir = await djconf.agetconfig('schools_dir', datapath + 'schools/')
      async for schoolline in dbschool.objects.filter(
          active = True, 
          tf_worker = self.dbline
      ):
        schooldir = schoolsdir + 'model' + str(schoolline.id) + '/'
        if not schoolline.dir:
          schoolline.dir = schooldir
          await schoolline.asave(update_fields=["dir"])
        await aiofiles.os.makedirs(schooldir + 'model/', exist_ok=True)
        await aiofiles.os.makedirs(schooldir + 'frames/', exist_ok=True)
        if self.dbline.use_litert:
          filename = schoolline.model_type + '.tflite'
        else:
          filename = schoolline.model_type + '.keras'
        dl_path = schooldir + 'model/' + filename
        if not await aiofiles.os.path.exists(dl_path):
          if self.dbline.use_litert:
            dl_url = ('https://static.cam-ai.de/models/standard/' 
              + schoolline.model_type 
              + '/litert/efficientnetv2-b0.tflite')
          else:
            dl_url = ('https://static.cam-ai.de/models/standard/' 
              + schoolline.model_type 
              + '/keras/efficientnetv2-b0.keras')
          async with aiohttp.ClientSession() as session:
            async with session.get(dl_url, allow_redirects=True) as response:
              async with aiofiles.open(dl_path, 'wb') as f:
                async for chunk in response.content.iter_chunked(65536):
                  await f.write(chunk) 
      #*** Common Vars
      self.is_ready = False
      #*** Server Var
      self.check_ts = time()
      self.models = {}
      self.active_models = 0
      #*** Client Var
      self.run_out_procs = {}
      self.model_check_lock = t_lock()
      self.ws_ts = None
      signal(SIGINT, sigint_handler)
      self.len_taglist = len(await asyncio.to_thread(get_taglist, 1))
      self.users = {}
      self.logname = 'tf_worker #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      self.model_buffers = {}
      self.load_model = None
      if self.dbline.gpu_sim >= 0: # Random values
        self.cachedict = {}
      elif self.dbline.use_websocket: # Websocket
        if self.dbline.wsname:
          await self.reset_websocket()
      else: #Local CPU or GPU
        if self.dbline.use_litert:
          if sysinfo()['hw'] == 'raspi':
            from tflite_runtime import interpreter as tflite
          else:
            from tensorflow import lite as tflite
          self.logger.info("*** Using LiteRT ***")
          self.tflite = tflite
        else:
          os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
          if self.dbline.gpu_nr == -1:
            os.environ["CUDA_VISIBLE_DEVICES"] = ''
          else:  
            os.environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.gpu_nr)
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
      self.is_ready = True
      schoolnr = 0
      print('Launch: tf_worker')
      await super().async_runner() 
      while self.do_run and not self.model_buffers:
        if self.dbline.use_websocket:
          await self.send_ping()
        await a_break_type(BR_LONG)
      self.finished = False
      wait_autos = {}
      while self.do_run:
        if self.dbline.use_websocket:
          await self.send_ping()
        while self.do_run:
          schoolnr += 1
          if schoolnr > max(self.model_buffers):
            schoolnr = 1
          if schoolnr in self.model_buffers:
            break
        if self.do_run:
          if self.model_buffers[schoolnr].pause:
            await a_break_type(BR_LONG)
          else: 
            if schoolnr not in wait_autos:
              wait_autos[schoolnr] = a_break_auto()  
            timeout = time() > self.model_buffers[schoolnr].ts + self.dbline.timeout
            if (schoolnr in self.model_buffers
                and (len(self.model_buffers[schoolnr]) >= self.dbline.maxblock
                or timeout)):
              wait_autos[schoolnr].reset()
              if self.do_run and len(self.model_buffers[schoolnr]):
                await self.process_buffer(schoolnr, self.logger, timeout)
              self.model_buffers[schoolnr].ts = time() 
            else:
              await wait_autos[schoolnr].wait() 
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
    except:
      from traceback import format_exc
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())

  async def send_ping(self):
    if self.ws_ts is None:
      return()
    if (time() - self.ws_ts) > 15:
      while True:
        try:
          await asyncio.to_thread(self.ws.send, 'Ping', opcode=1)
          self.ws_ts = time()
          break
        except (ConnectionResetError, OSError, BrokenPipeError):
          await a_break_type(BR_LONG)
          await self.reset_websocket()

  async def reset_websocket(self):
    from websockets import WebSocket
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
        await asyncio.to_thread(self.ws.send, json.dumps(outdict), opcode=1) #1 = Text
        await asyncio.to_thread(self.ws.recv)    
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
        await a_break_type(BR_LONG)

  async def continue_sending(self, payload, opcode=1, logger=None, get_answer=False):
    while self.do_run:
      while self.do_run:
        try:
          if opcode:
            await asyncio.to_thread(self.ws.send, payload, opcode = 1) # 1 = Text
            frameinfo = getframeinfo(currentframe())
          else:
            await asyncio.to_thread(self.ws.send_binary, payload)
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
          await a_break_type(BR_LONG)    
          await self.reset_websocket()
      if get_answer:
        try:
          return(await asyncio.to_thread(self.ws.recv))
        except (WebSocketTimeoutException, 
              WebSocketConnectionClosedException, 
              ConnectionRefusedError,
            ):
          if logger:
            logger.warning('Pipe error while reading in ' + frameinfo.filename 
              + ':' + str(frameinfo.lineno))
          await a_break_type(BR_LONG)
          await self.reset_websocket()
      else:
        return(None)
    

#***************************************************************************
#
# tf_worker server
#
#***************************************************************************

  async def check_model(self, schoolnr, logger, test_pred = False):
    if schoolnr not in self.models:
      self.models[schoolnr] = {}
      self.models[schoolnr]['dbline'] = await self.dbschool.objects.aget(id = schoolnr)
      self.models[schoolnr]['model_type'] = None
    school_dbline = self.models[schoolnr]['dbline']
    self.models[schoolnr]['last_check'] = time()
    if self.check_ts + 60.0 < time() and self.models[schoolnr]['model_type'] is not None:
      await school_dbline.arefresh_from_db()
      if (school_dbline.lastmodelfile is not None
          and	(datetime.timestamp(school_dbline.lastmodelfile) > self.models[schoolnr]['time']
          or school_dbline.model_type != self.models[schoolnr]['model_type']
          )):
        if schoolnr in self.model_buffers:  
          self.model_buffers[schoolnr].pause = True 
        self.models[schoolnr]['model_type'] = None   
        if self.dbline.gpu_sim < 0:
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
        await a_break_time(self.dbline.gpu_sim_loading)
      if self.dbline.gpu_sim >= 0:
        self.models[schoolnr]['xdim'] = 50
        self.models[schoolnr]['ydim'] = 50
      elif self.dbline.use_websocket:
        outdict = {
          'code' : 'get_xy',
          'scho' : school_dbline.e_school,
        }
        xytemp = json.loads(await self.continue_sending(json.dumps(outdict), 
          opcode=1, loggprocess_bufferer=logger, get_answer=True))
        self.models[schoolnr]['xdim'] = xytemp[0]
        self.models[schoolnr]['ydim'] = xytemp[1]
        await a_break_time(self.dbline.gpu_sim_loading)
        
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
          interpreter = await asyncio.to_thread(
            self.tflite.Interpreter, 
            model_path=model_path, 
            num_threads=2,
          )
          #interpreter = self.tflite.Interpreter(model_path=model_path, num_threads=2, )
          await asyncio.to_thread(interpreter.allocate_tensors)
          #interpreter.allocate_tensors()
          self.models[schoolnr]['model'] = interpreter
          self.models[schoolnr]['int_input'] = interpreter.tensor(
            interpreter.get_input_details()[0]["index"],
          )
          self.models[schoolnr]['int_output'] = interpreter.tensor(
            interpreter.get_output_details()[0]["index"],
          )
          self.models[schoolnr]['xdim'] = interpreter.get_input_details()[0]['shape_signature'][2]
          self.models[schoolnr]['ydim'] = interpreter.get_input_details()[0]['shape_signature'][1]
        else: 
          while self.load_model is None:
            await a_break_type(BR_LONG)
          loaded_model = await asyncio.to_thread(self.load_model, model_path)
          self.models[schoolnr]['model'] = loaded_model
          self.models[schoolnr]['xdim'] = loaded_model.layers[0].input_shape[2]
          self.models[schoolnr]['ydim'] = loaded_model.layers[0].input_shape[1]
        logger.info('***** Got model file #'+str(schoolnr) 
          + ', file: '+model_path)
      if test_pred and self.dbline.gpu_sim < 0:
        xdata = np.random.rand(8,self.models[schoolnr]['xdim'],
          self.models[schoolnr]['ydim'],3)
        if self.dbline.use_litert: 
          logger.info(str(self.models[schoolnr]['model'].get_input_details()[0]))
          self.models[schoolnr]['int_input']().fill(128)
          self.models[schoolnr]['model'].invoke()

        else:
          loaded_model = await asyncio.to_thread(
            self.models[schoolnr]['model'].predict_on_batch, 
            xdata, 
          )
        logger.info('***** Testrun for model #' + str(schoolnr)+', type: '
          + self.models[schoolnr]['model_type'])
      self.active_models += 1

  async def process_buffer(self, schoolnr, logger, had_timeout=False):
    mybuffer = self.model_buffers[schoolnr]
    ts_one = time()
    slice_to_process = mybuffer.get(self.dbline.maxblock)
    framelist = [item[0] for item in slice_to_process]
    framesinfo = [item[1] for item in slice_to_process]
    await self.check_model(schoolnr, logger, True)
    self.model_buffers[schoolnr].pause = False
    if self.dbline.gpu_sim >= 0: #GPU Simulation with random
      if self.dbline.gpu_sim > 0:
        await a_break_time(self.dbline.gpu_sim)
      predictions = np.empty((0, self.len_taglist), np.float32)
      for i in framelist:
        myindex = round(np.sum(i).item())
        if myindex in self.cachedict:
          line = self.cachedict[myindex]
        else:
          line = []
          for j in range(self.len_taglist):
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
          await self.continue_sending(json.dumps(outdict), 
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
            jpgdata = await asyncio.to_thread(
              lambda: cv.imencode('.jpg', 
              item)[1].tobytes(), 
            )
            schoolbytes = models[schoolnr]['dbline'].e_school.to_bytes(8, 'big')
            await self.continue_sending(schoolbytes+jpgdata, opcode=0, 
              logger=logger, get_answer=False)
          outdict = {
            'code' : 'done',
            'scho' : models[schoolnr]['dbline'].e_school,
          }
          predictions = await self.continue_sending(json.dumps(outdict), opcode=1, 
            logger=logger, get_answer=True)
          try:  
            predictions = json.loads(predictions) 
          except json.decoder.JSONDecodeError:
            self.logger.error('Error in process: ' + self.logname)
            self.logger.error(format_exc())
            self.logger.error('***** Received predictions: *' + str(predictions) + '*')
            predictions = None  
          if predictions is None:
            predictions = np.zeros((len(framelist), self.len_taglist), np.float32)
          else:
            predictions = np.array(predictions, dtype=np.float32)
          break
        except (ConnectionResetError, OSError):
          await a_break_type(BR_LONG)
          await self.reset_websocket()
    else: #local GPU
      if self.dbline.use_litert: #Predictions Tensorflow Lite
        predictions = np.empty((0, self.len_taglist), np.float32)
        for item in framelist:
          np.copyto(self.models[schoolnr]['int_input'](), item)
          await asyncio.to_thread(self.models[schoolnr]['model'].invoke)
          #self.models[schoolnr]['model'].invoke()
          line=np.zeros((1, self.len_taglist), np.float32)
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
          predictions = await asyncio.to_thread(
            self.models[schoolnr]['model'].predict_on_batch, npframelist
          )
        else:
          logger.warning('Defective image in c_tfworkers / processbuffer') 
          predictions = None  
    if predictions is not None:
      starting = 0
      for i in range(len(framelist)):
        if ((i == len(framelist) - 1) 
            or (framesinfo[i] != framesinfo[i+1])):
          if (framesinfo[starting] in self.users):
            await self.my_output.put(framesinfo[starting], (
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

#***************************************************************************
#
# tf_worker client
#
#***************************************************************************

class tf_worker_client():
  def __init__(self, inqueue, registerqueue, ):
    self.inqueue = inqueue
    self.registerqueue = registerqueue
    self.run_out_procs = {}
    self.pred_out_dict = {}
    self.pred_out_lock = t_lock()
    self.is_ready = None
    self.auto_break = a_break_auto(tmin = 0.01, tmax = 0.1, rate = 0.01)

  async def out_reader_proc(self, index): #called by client (c_eventer)
    try:
      while True:
        received = await self.my_output.get(index)
        #print('##### Out_Reader:', received)
        if (received[0] == 'stop'):
          break
        elif (received[0] == 'put_is_ready'):
          self.is_ready = received[1]
        elif (received[0] == 'put_xy'):
          self.xy = received[1]
        elif (received[0] == 'pred_to_send'):
          while True:
            with self.pred_out_lock:
              if  received[2] not in self.pred_out_dict:
                self.pred_out_dict[received[2]] = None
              if self.pred_out_dict[received[2]] is None:
                self.pred_out_dict[received[2]] = received[1]
                self.auto_break.reset()
                break
            await self.auto_break.wait()   
        else:
          raise QueueUnknownKeyword(received[0])
    except:
      self.logger.error('Error in process: ' + self.logname + ' (out_reader_proc)')
      self.logger.error(format_exc())

  async def register(self, worker_id):
    await self.inqueue.put(('register', 0, ))
    self.tf_w_index = await asyncio.to_thread(self.registerqueue.get)
    self.id = worker_id
    self.my_output = output_dist(self.id)
    self.my_output.clean_one(self.tf_w_index)
    return(self.tf_w_index)

  async def run_out(self, index):
    self.run_out_procs[index] = asyncio.create_task(
      self.out_reader_proc(index, ), 
      name = 'run_out_task', 
    )
    return(self.tf_w_index)

  async def unregister(self, tf_w_index):
    await self.inqueue.put(('unregister', tf_w_index, ))

  async def check_ready(self, tf_w_index):
    if not self.is_ready:
      self.is_ready = None
      await self.inqueue.put(('get_is_ready', tf_w_index))
      while self.is_ready is None:
        await self.auto_break.wait()    
      self.auto_break.reset()  
    return(self.is_ready)

  async def get_xy(self, school, tf_w_index):
    self.xy = None
    await self.inqueue.put(('get_xy', tf_w_index, school))
    while self.xy is None:
      await self.auto_break.wait()   
    self.auto_break.reset()  
    return(self.xy)

  async def ask_pred(self, school, image_list, tf_w_index):
    command_line = ['ask_pred', tf_w_index, school, ]
    command_line += image_list
    await self.inqueue.put(command_line)

  async def client_check_model(self, tf_w_index, schoolnr, test_pred = False):
    await self.inqueue.put((
      'checkmod', 
      tf_w_index, 
      schoolnr, 
      test_pred,
    ))

  def outqueue_empty(self, userindex):
    with self.pred_out_lock:
      result = ((userindex not in self.pred_out_dict) 
        or (self.pred_out_dict[userindex] is None))
    return(result)

  async def get_from_outqueue(self, userindex):
    while True:
      with self.pred_out_lock:
        if userindex in self.pred_out_dict and self.pred_out_dict[userindex] is not None:
          result = self.pred_out_dict[userindex]
          self.pred_out_dict[userindex] = None
          self.auto_break.reset()  
          return(result)
      await self.auto_break.wait()   

  async def stop_out(self, index):
    await self.my_output.put(index, ('stop',))
    self.run_out_procs[index].join()
