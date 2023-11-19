# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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

from os import path, rename, environ, makedirs
from sys import platform
from random import seed, uniform, shuffle, random
from shutil import copyfile
from time import time
import numpy as np
from traceback import format_exc
from math import ceil, sqrt, pi, log
from setproctitle import setproctitle
from logging import getLogger
from django.utils import timezone
from django.db import connection as sqlconnection
from tensorflow.keras.utils import Sequence
from tensorflow.keras.callbacks import (EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, 
  Callback)
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import (InputLayer, Dropout)
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from tensorflow.keras.constraints import max_norm
from keras_cv.layers import RandAugment
from tools.l_tools import djconf
from tools.c_tools import cmetrics, hit100
from tools.c_logger import log_ini
from schools.c_schools import get_tagnamelist
from .models import trainframe, fit as sqlfit, epoch
from .make_model import make_model

load_model = None
tf = None

DO_AUGMENTATION = True

RAND_AUGMENT_MAGNITUDE = 0.01

class sql_sequence(Sequence):
  def __init__(self, logger, sqlresult, xdim, ydim, myschool, 
      batch_size=32, 
      class_weights=None, 
      model=None,
    ):
    self.logger = logger
    self.sqlresult = sqlresult
    self.batch_size = batch_size
    self.xdim = xdim
    self.ydim = ydim
    self.class_weights = class_weights
    self.model = model
    self.classes_list = get_tagnamelist(1)
    self.myschool = myschool
    self.ram_buffer = {}

  def __len__(self):
    return ceil(len(self.sqlresult) / self.batch_size)

  def __getitem__(self, idx):
    batch_slice = self.sqlresult[idx*self.batch_size:(idx + 1)*self.batch_size]
    xdata = []
    ydata = np.empty(shape=(len(batch_slice), len(self.classes_list)))
    for i in range(len(batch_slice)):
      bmp_file_path = batch_slice[i][1]
      cod_file_path = (bmp_file_path[:-4]+'.cod').replace('/frames/', '/coded/'+str(self.xdim)+'x'+str(self.ydim)+'/')
      ram_cod_id = batch_slice[i][0]
      done = False
      try:
        if ram_cod_id in self.ram_buffer:
          imgdata = tf.convert_to_tensor(self.ram_buffer[ram_cod_id])
          storedata = None
          imgdata =  tf.io.decode_jpeg(imgdata);
          done = True
        else:
          if path.exists(cod_file_path):
            imgdata = tf.io.read_file(cod_file_path)
            storedata = imgdata
            imgdata =  tf.io.decode_jpeg(imgdata);
            done = True
        if done and ((imgdata.shape[0] != self.xdim) or (imgdata.shape[1] != self.ydim)):
          done = False
        if not done:  
          imgdata = tf.io.read_file(bmp_file_path)
          imgdata = tf.io.decode_bmp(imgdata, channels=3)
          imgdata = tf.image.resize(imgdata, [self.xdim,self.ydim], antialias=True)
          imgdata = tf.cast(imgdata, tf.uint8)
          storedata = tf.io.encode_jpeg(imgdata);
          tf.io.write_file(cod_file_path, storedata)
        if storedata:  
          self.ram_buffer[ram_cod_id] = storedata.numpy()
      except:
        self.logger.info('***** Error in reading/decoding:'+batch_slice[i][1])
        exit(1)
      xdata.append(imgdata)
      for j in range(len(self.classes_list)):
        ydata[i][j] = batch_slice[i][j+2]
    xdata = tf.stack(xdata)
    ydata = tf.convert_to_tensor(ydata)

    if self.class_weights is not None:
      wdata = np.zeros(shape=(len(batch_slice)))

      predictions = self.model.predict_on_batch(xdata)
      for i in range(len(batch_slice)):
        wdata[i] = 0.0
        nothing_found = True
        for j in range(len(self.class_weights)-1):
          if ydata[i,j]:
            wdata[i] += self.class_weights[j]
            if nothing_found:
              nothing_found = False
        if nothing_found:
          wdata[i] = self.class_weights[len(self.class_weights) - 1]

        for j in range(len(self.classes_list)):
          if round(predictions[i][j]) != ydata[i][j]:
            wdata[i] += self.myschool.weight_boost;
            
    if self.class_weights is None:
      return(xdata, ydata)
    else:
      return(xdata, ydata, wdata)

  def on_epoch_end(self):
    if self.class_weights is not None:
      shuffle(self.sqlresult)

class MyCallback(Callback):
  def __init__(self, myfit, logger, myschool):
    super().__init__()
    self.myfit = myfit
    self.logger = logger
    self.ts_start = timezone.now()
    self.epoch_count = 0
    self.myfit.early_stop_delta_min = myschool.early_stop_delta_min 
    self.myfit.early_stop_patience = myschool.early_stop_patience
    self.myfit.l_rate_start = myschool.l_rate_start
    self.myfit.l_rate_stop = myschool.l_rate_stop
    self.myfit.l_rate_delta_min = myschool.l_rate_delta_min
    self.myfit.l_rate_patience = myschool.l_rate_patience
    self.myfit.l_rate_decrement = myschool.l_rate_decrement
    self.myfit.weight_min = myschool.weight_min
    self.myfit.weight_max = myschool.weight_max
    self.myfit.weight_boost = myschool.weight_boost
    self.myfit.model_type = myschool.model_type
    self.myfit.model_image_augmentation = myschool.model_image_augmentation
    self.myfit.model_weight_decay = myschool.model_weight_decay
    self.myfit.model_weight_constraint = myschool.model_weight_constraint
    self.myfit.model_dropout = myschool.model_dropout
    self.myfit.model_stop_overfit = myschool.model_stop_overfit
    self.myfit.save()

  def on_epoch_begin(self, myepoch, logs=None):
    self.starttime = time()

  def on_epoch_end(self, myepoch, logs=None):
    self.epoch_count += 1
    secondstime = time() - self.starttime
    logstring = 'E'+str(myepoch)+': '
    logstring += str(round(secondstime)).rjust(4)+'s  '
    logstring += 'loss = '+str(round(logs['loss'],5)).ljust(7,'0')+'  '
    logstring += 'hit100 = '+str(round(logs['hit100'],5)).ljust(7,'0')+'  '
    logstring += 'cmetrics = '+str(round(logs['cmetrics'],5)).ljust(7,'0')+'  '
    logstring += 'val_loss = '+str(round(logs['val_loss'],5)).ljust(7,'0')+'  '
    logstring += 'val_hit100 = '+str(round(logs['val_hit100'],5)).ljust(7,'0')+'  '
    logstring += 'val_cmetrics = '+str(round(logs['val_cmetrics'],5)).ljust(7,'0')+'  '
    logstring += 'lr = '+str(logs['lr'])
    self.logger.info(logstring)
    myepoch = epoch(fit=self.myfit, 
      loss = logs['loss'],
      cmetrics = logs['cmetrics'],
      hit100 = logs['hit100'],
      val_loss = logs['val_loss'],
      val_cmetrics = logs['val_cmetrics'],
      val_hit100 = logs['val_hit100'],
      seconds = secondstime,
      learning_rate = log(logs['lr'], 10.0)
    )
    myepoch.save()
    self.myfit.loss = logs['loss']
    self.myfit.cmetrics = logs['cmetrics']
    self.myfit.hit100 = logs['hit100']
    self.myfit.val_loss = logs['val_loss']
    self.myfit.val_cmetrics = logs['val_cmetrics']
    self.myfit.val_hit100 = logs['val_hit100']
    self.myfit.minutes = (timezone.now() - self.ts_start).total_seconds() / 60
    self.myfit.epochs = self.epoch_count
    self.myfit.save()
    sqlconnection.close()
    if self.myfit.model_stop_overfit and logs['loss'] < logs['val_loss']:
      self.logger.info('*** Epoch ' + str(self.epoch_count) + ': Stopping overfitting...')
      self.model.stop_training = True

def gpu_init(gpu_nr, gpu_mem_limit, logger):
  try:
    global load_model
    global tf
    environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
    if gpu_nr == -1:
      environ["CUDA_VISIBLE_DEVICES"] = ''
    else:  
      environ["CUDA_VISIBLE_DEVICES"]=str(gpu_nr)
    import tensorflow as tf
    if (gpu_mem_limit) and (gpu_nr >= 0):
      gpus = tf.config.list_physical_devices('GPU')
      for gpu in gpus:
        tf.config.set_logical_device_configuration(
            gpu, [tf.config.LogicalDeviceConfiguration(memory_limit=gpu_mem_limit)])
      logical_gpus = tf.config.list_logical_devices('GPU')
      logger.info(str(len(gpus))+" Physical GPUs, " + str(len(logical_gpus))
        + " Logical GPUs")
    from tensorflow.keras.models import load_model
    logger.info("TensorFlow version: "+tf.__version__)
    device_name = tf.test.gpu_device_name()
    if device_name:
	    logger.info('Found GPU at: '+device_name)
    else:
	    logger.info('GPU device not found')
  except:
    logger.error(format_exc())
    logger.handlers.clear()

def getlines(myschool, logger):
  filterdict = {}
  filterdict['school'] = myschool.id
  if not myschool.ignore_checked:
    filterdict['checked'] = True
  filterdict['train_status__gt'] = 0
  filterdict['code'] = 'TR'
  trcount = trainframe.objects.filter(**filterdict).count()
  filterdict['code'] = 'VA'
  vacount = trainframe.objects.filter(**filterdict).count()
  filterdict['code'] = 'NE'
  idlines = trainframe.objects.filter(**filterdict).values_list('id', flat=True)
  logger.info('My Model: TR '+str(trcount)+', VA '+str(vacount)+', NE '+str(len(idlines)))
  for idline in idlines:
    if (((trcount + vacount) == 0) or
      ((vacount / (trcount + vacount)) 
        >= djconf.getconfigfloat('validation_split', 0.33333333))):
      newcode = 'TR'
      trcount += 1
    else:
      newcode = 'VA'
      vacount += 1
    line = trainframe.objects.get(id=idline)
    line.code = newcode
    line.save(update_fields=["code"])
  result = {}
  for code in ['TR', 'VA']:
    filterdict['code'] = code
    result[code] = []
    for item in trainframe.objects.filter(**filterdict):
      resultitem = [item.id, myschool.dir + 'frames/' + item.name, item.c0, item.c1, 
        item.c2, item.c3, item.c4, item.c5, item.c6, item.c7,
        item.c8, item.c9, item.code,
      ]
      result[code].append(resultitem)
  logger.info('Updatetd Model: TR '+str(len(result['TR']))+', VA'+str(len(result['VA'])))
  return(result)

def train_once_gpu(myschool, myfit, gpu_nr, gpu_mem_limit):
  logname = 'GPU #'+str(gpu_nr)
  logger = getLogger(logname)
  log_ini(logger, logname)
  setproctitle('CAM-AI-GPU #' + str(gpu_nr))
  logger.info('***Launching GPU#' + str(gpu_nr) + ', MemLimit: ' + str(gpu_mem_limit))
  gpu_init(gpu_nr, gpu_mem_limit, logger)
  seed()
  epochs = djconf.getconfigint('tr_epochs', 1000)
  batchsize = djconf.getconfigint('tr_batchsize', 32)
  val_split = djconf.getconfigfloat('validatiothn_split', 0.33333333)
  mypatience = myschool.early_stop_patience
  classes_list = get_tagnamelist(myschool.id)

  logger.info('*******************************************************************');
  logger.info('*** Working on School #'+str(myschool.id)+', '+myschool.name+'...');
  logger.info('*******************************************************************');

  templist = getlines(myschool, logger)
  trlist = templist['TR']
  valist = templist['VA']

  myfit.made = timezone.now()
  myfit.nr_tr = len(trlist)
  myfit.nr_va = len(valist)
  myfit.status = "Working"
  myfit.save(update_fields=["made", "nr_tr", "nr_va", "status"])

  weightarray = [0] * (len(classes_list) + 1)

  model_name = myschool.model_type
  modelpath = myschool.dir + 'model/'
  if path.exists(modelpath + model_name + '.extra.h5'):
    extra_model_found = True
    model_to_load = modelpath + model_name + '.extra.h5'
  else:  
    extra_model_found = False
    if path.exists(modelpath + model_name + '.h5'):
      if myschool.save_new_model:
        if sqlfit.objects.filter(school=myschool.id).exists():
          fitnr = sqlfit.objects.filter(school=myschool.id).latest('id').id
        else:
          fitnr = -1
        copyfile(modelpath + model_name + '.h5', 
          modelpath + model_name + '_' + str(fitnr) + '.h5')
      model_to_load = modelpath + model_name + '.h5'
    else:
      school1model = djconf.getconfig('schools_dir', 'data/schools/') + 'model1/model/' + model_name + '.h5'
      if (myschool.id != 1) and path.exists(school1model):
        model_to_load = school1model
      else:
        model_to_load = None
  if model_to_load:     
    logger.info('*** Loading model ' + model_to_load);
    model = load_model(model_to_load, 
      custom_objects={'cmetrics': cmetrics, 'hit100': hit100,})
  else:    
    logger.info('*** Creating model: ' + modelpath + model_name + '.h5');
    model = make_model(model_name, len(classes_list))
  xdim = model.layers[0].input_shape[1]
  ydim = model.layers[0].input_shape[2]
  lcopy = [item for item in model.layers]
  for item in model.layers:
    if item.name == model_name:
      break
    else:
      lcopy.pop(0)
  count = 0    
  for item in lcopy:
    if item.name[:6] == 'CAM-AI':
      count += 1
  if count == 4: 
    lcopy = [item for item in lcopy if ((item.name == model_name) or (item.name[:6] == 'CAM-AI'))]
  if myschool.model_weight_decay:
    lcopy[2].kernel_regularizer = l2(myschool.model_weight_decay)
    lcopy[2].bias_regularizer = l2(myschool.model_weight_decay)
    lcopy[3].kernel_regularizer = l2(myschool.model_weight_decay)
    lcopy[3].bias_regularizer = l2(myschool.model_weight_decay)
  else:  
    lcopy[2].kernel_regularizer = None
    lcopy[2].bias_regularizer = None
    lcopy[3].kernel_regularizer = None
    lcopy[3].bias_regularizer = None
  if myschool.model_weight_constraint:
    lcopy[2].kernel_constraint = max_norm(myschool.model_weight_constraint)
    lcopy[2].bias_constraint = max_norm(myschool.model_weight_constraint)
    lcopy[3].kernel_constraint = max_norm(myschool.model_weight_constraint)
    lcopy[3].bias_constraint = max_norm(myschool.model_weight_constraint)
  else:
    lcopy[2].kernel_constraint = None
    lcopy[2].bias_constraint = None
    lcopy[3].kernel_constraint = None
    lcopy[3].bias_constraint = None
  if myschool.model_dropout:
    lcopy.insert(4, Dropout(myschool.model_dropout))
    lcopy.insert(3, Dropout(myschool.model_dropout))
    lcopy.insert(2, Dropout(myschool.model_dropout))
  model = Sequential(lcopy)
    
  if myschool.model_image_augmentation: 
    layers = [item for item in model.layers]
    layers.insert(0, RandAugment(
      magnitude = myschool.model_image_augmentation,
      value_range = (0,255),
      ))
    layers.insert(0, InputLayer(
      input_shape = (model.layers[0].input_shape[1:]), 
    ))
           
    model = Sequential(layers)
  if not(path.exists(myschool.dir+'coded/'+str(xdim)+'x'+str(ydim))):
    makedirs(myschool.dir+'coded/'+str(xdim)+'x'+str(ydim))
  l_rate = float(myschool.l_rate_start)
  logger.info('>>> New learning rate: '+str(l_rate))
  model.compile(loss='binary_crossentropy',
    optimizer=Adam(learning_rate=l_rate),
    metrics=[hit100, cmetrics])
  model.summary(print_fn=lambda x: logger.info(x))
  for item in trlist:
    found_class = False
    for count in range(len(classes_list)):
	    if item[count+2] >= 0.5:
		    weightarray[count] += 1
		    found_class = True
    if (not found_class):
	    weightarray[len(classes_list)] += 1

  class_weights = [myschool.weight_max 
    - ((x * (myschool.weight_max - myschool.weight_min)) 
     / max(weightarray)) for x in weightarray]

  train_sequence = sql_sequence(logger, trlist, xdim, ydim, myschool,
    batch_size=batchsize, 
    class_weights=class_weights, 
    model=model,
  )

  vali_sequence = sql_sequence(logger, valist, xdim, ydim, myschool,
    batch_size=batchsize)

  es = EarlyStopping(monitor = 'val_loss', mode = 'min', verbose = 0,
    min_delta = myschool.early_stop_delta_min, patience = myschool.early_stop_patience)
  mc = ModelCheckpoint(myschool.dir + 'model/' + model_name + '_temp.h5', 
    monitor = 'val_loss', mode = 'min', verbose = 0, save_best_only = True)
  reduce_lr = ReduceLROnPlateau(monitor = 'val_loss', mode = 'min', 
    factor = myschool.l_rate_decrement, patience = myschool.l_rate_patience, 
    min_lr = float(myschool.l_rate_stop), min_delta = myschool.l_rate_delta_min, 
    verbose = 0)
  cb = MyCallback(myfit, logger, myschool)

  sqlconnection.close()

  history = model.fit(
    x=train_sequence,
    validation_data=vali_sequence,
    shuffle=False,
    epochs=epochs, 
    verbose=0,
    callbacks=[es, mc, reduce_lr, cb,],
    )

  if (myschool.save_new_model or extra_model_found):
    rename(myschool.dir+'model/'+model_name+'_temp.h5', 
      myschool.dir+'model/'+model_name+'.h5')
  if extra_model_found:
    rename(myschool.dir+'model/'+model_name+'.extra.h5', 
      myschool.dir+'model/'+model_name+'.old_extra.h5')

  myschool.lastmodelfile = timezone.now()
  myschool.save(update_fields=["lastmodelfile"])

  if len(history.history['loss'])	>= epochs:
    mypatience = 0
  epochs = len(history.history['loss'])	
  if epochs < mypatience + 1:
    mypatience = epochs - 1 
  myfit.epochs = epochs
  myfit.loss = float(history.history['loss'][epochs-mypatience-1])
  myfit.cmetrics = float(history.history['cmetrics'][epochs-mypatience-1])
  myfit.hit100 = float(history.history['hit100'][epochs-mypatience-1])
  myfit.val_loss = float(history.history['val_loss'][epochs-mypatience-1])
  myfit.val_cmetrics = float(history.history['val_cmetrics'][epochs-mypatience-1])
  myfit.val_hit100 = float(history.history['val_hit100'][epochs-mypatience-1])
  myfit.status = 'Done'
  myfit.save(update_fields=[
    "minutes", "epochs", "loss", "cmetrics", "hit100", 
    "val_loss", "val_cmetrics", "val_hit100", "status"])

  logger.info('***  Done  ***')
