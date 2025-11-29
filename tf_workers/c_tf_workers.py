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

import os
import json
import numpy as np
import cv2 as cv
import pickle
import asyncio
import aiofiles
import aiohttp
import itertools
from multiprocessing import Queue as p_queue, SimpleQueue as s_queue
from time import time
from datetime import datetime
from threading import Lock as t_lock
from random import random
from logging import getLogger
from signal import signal, SIGINT
from statistics import mean
from channels.db import database_sync_to_async
from setproctitle import setproctitle
from tools.l_sysinfo import sysinfo
from tools.l_break import (a_break_time, a_break_type, break_type, a_break_auto, 
  BR_SHORT, BR_MEDIUM, BR_LONG, )
from tools.c_redis import my_redis as safe_redis
from .redis import my_redis as tf_workers_redis

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

class model_buffer(asyncio.PriorityQueue):

  def __init__(self, schoolnr, xdim, ydim):
    super().__init__()
    self._counter = itertools.count()
    self.ts = time()
    self.xdim = xdim
    self.ydim = ydim
    self.pause = True

  async def append(self, initem, prio):
    # structure of initem:
    # initem[0] = userindex, schoolnr, initem[1] = np.image, initem[2] = np.image...
    # structure of outitem:
    # outitem[0] = np.image, outitem[1] = userindex
    if self.pause:
      await a_break_type(BR_LONG)
      return()
    for frame in initem[2:]:
      if frame.shape[1] != self.xdim or  frame.shape[0] != self.ydim:
        frame = await asyncio.to_thread(cv.resize, frame, (self.xdim, self.ydim))
      cnt = next(self._counter) 
      await super().put((prio, cnt, (frame, initem[0])))

  async def get(self, maxcount):
    result = []
    while True:
      if self.empty():
        break
      else:  
        outitem = (await super().get())[2]
        #prio, count, outitem = (await super().get())
      result.append(outitem)
      if len(result) >= maxcount:
        break 
    return(result)

class tf_user(object):
  clientset = set()

  def __init__(self, prio = 4):
      i = 0
      while (i in self.clientset):
        i += 1
      self.clientset.add(i)
      self.id = i 
      self.prio = prio

  def __del__(self):
      self.clientset.discard(self.id)
      
class output_dist():   
  def __init__(self, tf_worker):
    self.nametag = 'cam-ai.tf_worker.output:' + str(tf_worker.id) + ':'
    self.used_adresses = set()
    self.auto_break = a_break_auto(tmin = 0.01, tmax = 0.1, rate = 0.01)
    self.tf_worker = tf_worker
    
  async def put(self, tf_w_index, data):
    while (not getattr(self.tf_worker, 'got_sigint', False)
        and safe_redis.exists(self.nametag + str(tf_w_index) + ':')): 
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
    
  def _safe_maxblock(self) -> int:
    return(self.dbline.maxblock)
    #if self.dbline.use_litert:
    #  return(1)
    #else:  
    #  return(self.dbline.maxblock)
    
  async def process_received(self, received):  
    result = True
    #print('TF-Worker-Inqueue received:', received[:3], len(received))
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
      if len(received) == 3: #no images
        return(True)
      while not 'xdim' in self.models[schoolnr]:
        await a_break_type(BR_LONG)
      if schoolnr not in self.model_buffers:
        self.model_buffers[schoolnr] = model_buffer(schoolnr, 
          self.models[schoolnr]['xdim'], 
          self.models[schoolnr]['ydim'],
        )
      self.model_buffers[schoolnr].pause = False
      await self.model_buffers[schoolnr].append(
        received[1:], 
        self.users[received[1]].prio,
      )
    elif (received[0] == 'register'):
      myuser = tf_user(prio = received[1])
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
      self.got_sigint = False
      self.my_output = output_dist(self)
      datapath = await djconf.agetconfig('datapath', 'data/')
      self.do_tf_debug = await djconf.agetconfigbool('do_tf_debug', True)
      if self.do_tf_debug:
        tf_debug_buf_count = 9
        self.tf_debug_block_count = 9
        tf_debug_ts = 0.0
        buf_size = 0
        buf_size_10 = 0.0
        buf_size_list = [0]
        self.block_size_list = [0]
        self.proc_time_list = [0.0]
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
      self.ws_ts = None
      #signal(SIGINT, sigint_handler)
      self.len_taglist = len(await database_sync_to_async(get_taglist)(1, ))
      self.users = {}
      self.logname = 'tf_worker #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      self.model_buffers = {}
      self.load_model = None
      if self.dbline.gpu_sim >= 0: # Random values
        self.cachedict = {}
      else: #Local CPU or GPU
        if self.dbline.use_litert:
          from ai_edge_litert import interpreter as tflite
          from ai_edge_litert.interpreter import load_delegate
          #if self.dbline.use_coral or sysinfo()['hw'] == 'raspi':
          #  from tflite_runtime import interpreter as tflite
          #else:
          #  from ai_edge_litert import interpreter as tflite
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
      #print('Launch: tf_worker')
      await super().async_runner() 
      while not (self.got_sigint or self.model_buffers):
        await a_break_type(BR_LONG)
      self.finished = False
      wait_autos = {}
      while not self.got_sigint:
        while not self.got_sigint:
          schoolnr += 1
          if schoolnr > max(self.model_buffers):
            schoolnr = 1
          if schoolnr in self.model_buffers:
            break
        if self.do_tf_debug and time() - tf_debug_ts >= 1.0:
          buf_size = self.model_buffers[schoolnr].qsize()
          if tf_debug_buf_count >= 9:
            buf_size_10 = mean(buf_size_list)
            buf_size_list = [buf_size]
            tf_debug_buf_count = 0
          else:
            buf_size_list.append(buf_size)
            tf_debug_buf_count += 1  
          tf_workers_redis.set_buf_size(self.id, buf_size)
          tf_workers_redis.set_buf_size_10(self.id, buf_size_10)
        if not self.got_sigint:
          if self.model_buffers[schoolnr].pause:
            await a_break_type(BR_LONG)
          else: 
            if schoolnr not in wait_autos:
              wait_autos[schoolnr] = a_break_auto()  
            timeout = time() > self.model_buffers[schoolnr].ts + self.dbline.timeout
            if (schoolnr in self.model_buffers
                and (self.model_buffers[schoolnr].qsize() >= self._safe_maxblock()
                or timeout)):
              wait_autos[schoolnr].reset()
              if not self.got_sigint and not self.model_buffers[schoolnr].empty():
                await self.process_buffer(schoolnr, self.logger, timeout)
              self.model_buffers[schoolnr].ts = time() 
            else:
              await wait_autos[schoolnr].wait() 
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
    except Exception as fatal:
      self.logger.error(
        'Error in process: ' + self.logname)
      self.logger.critical("async_runner crashed: %s", fatal, exc_info=True)

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
      self.check_ts = time()
      if (
        school_dbline.last_fit != self.models[schoolnr]['fit_nr']
        or school_dbline.model_type != self.models[schoolnr]['model_type']
      ):
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
      if self.dbline.gpu_sim >= 0: #simulation
        self.models[schoolnr]['fit_nr'] = 1
        self.models[schoolnr]['model_type'] = 'simulation'
      else:  #lokal GPU
        self.models[schoolnr]['fit_nr'] = school_dbline.last_fit
        self.models[schoolnr]['model_type'] = school_dbline.model_type
        await a_break_time(self.dbline.gpu_sim_loading)
      if self.dbline.gpu_sim >= 0:
        self.models[schoolnr]['xdim'] = 50
        self.models[schoolnr]['ydim'] = 50
      else: #lokal GPU
        if self.dbline.use_litert:
          if self.dbline.use_coral:
            model_path = (school_dbline.dir 
              + 'model/c' + school_dbline.model_type + '.tflite')
          else:
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
          if self.dbline.use_coral:
            interpreter = await asyncio.to_thread(
              self.tflite.Interpreter, 
              model_path = model_path, 
              experimental_delegates=[load_delegate('libedgetpu.so.1')],
            )
          else:
            interpreter = await asyncio.to_thread(
              self.tflite.Interpreter, 
              model_path = model_path, 
            )
          print('00000', interpreter._delegates)
          await asyncio.to_thread(interpreter.allocate_tensors)
          print('11111', interpreter._delegates)
          self.models[schoolnr]['model'] = interpreter
          self.models[schoolnr]['int_input'] = interpreter.tensor(
            interpreter.get_input_details()[0]["index"],
          )
          self.models[schoolnr]['int_output'] = interpreter.tensor(
            interpreter.get_output_details()[0]["index"],
          )
          self.models[schoolnr]['xdim'] = (
            interpreter.get_input_details()[0]['shape_signature'][2]
          )  
          self.models[schoolnr]['ydim'] = (
            interpreter.get_input_details()[0]['shape_signature'][1]
          )
        else: 
          while self.load_model is None:
            await a_break_type(BR_LONG)
          loaded_model = await asyncio.to_thread(self.load_model, model_path)
          self.models[schoolnr]['model'] = loaded_model
          self.models[schoolnr]['xdim'] = loaded_model.input_shape[2]
          self.models[schoolnr]['ydim'] = loaded_model.input_shape[1]
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
    slice_to_process = await mybuffer.get(self._safe_maxblock())
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
    else: #local GPU
      if self.dbline.use_litert: #Predictions Tensorflow Lite
        predictions = np.empty((0, self.len_taglist), np.float32)
        for item in framelist:
          np.copyto(self.models[schoolnr]['int_input'](), item)
          await asyncio.to_thread(self.models[schoolnr]['model'].invoke)
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
      if self.do_tf_debug:
        block_size = len(framelist)
        proc_time = time() - ts_one  
        if self.tf_debug_block_count >= 9:
          self.block_size_10 = mean(self.block_size_list)
          self.block_size_list = [block_size]
          self.proc_time_10 = mean(self.proc_time_list)
          self.proc_time_list = [proc_time]
          self.tf_debug_block_count = 0
        else:
          self.block_size_list.append(block_size)
          self.proc_time_list.append(proc_time)
          self.tf_debug_block_count += 1  
        tf_workers_redis.set_block_size(self.id, block_size)
        tf_workers_redis.set_block_size_10(self.id, self.block_size_10)
        tf_workers_redis.set_proc_time(self.id, proc_time)
        tf_workers_redis.set_proc_time_10(self.id, self.proc_time_10)

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
    self.prio_dict = {}

  async def out_reader_proc(self, index): #called by client (c_eventer)
    try:
      while True:
        received = await self.my_output.get(index)
        #print('Out_Reader received:', received)
        if (received[0] == 'stop'):
          break
        elif (received[0] == 'put_is_ready'):
          self.is_ready = received[1]
        elif (received[0] == 'put_xy'):
          self.xy = received[1]
        elif (received[0] == 'pred_to_send'):
          while True:
            with self.pred_out_lock:
              if received[2] not in self.pred_out_dict:
                self.pred_out_dict[received[2]] = None
              if self.pred_out_dict[received[2]] is None:
                self.pred_out_dict[received[2]] = received[1]
                self.auto_break.reset()
                break
            await self.auto_break.wait() 
        else:
          raise QueueUnknownKeyword(received[0])
    except Exception as fatal:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.critical("out_reader_proc crashed: %s", fatal, exc_info=True)

  async def register(self, worker_id, prio = 4):
    await self.inqueue.put(('register', prio, ))
    self.tf_w_index = await asyncio.to_thread(self.registerqueue.get)
    self.id = worker_id
    self.my_output = output_dist(self)
    self.my_output.clean_one(self.tf_w_index)
    self.prio_dict[self.tf_w_index] = prio
    return(self.tf_w_index)

  async def run_out(self, index, logger, logname):
    self.logger = logger
    self.logname = logname
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
    if self.prio_dict[self.tf_w_index] < 6:
      tf_workers_redis.set_last_prio_write()
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
    await self.run_out_procs[index]
