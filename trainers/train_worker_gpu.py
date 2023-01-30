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

from os import path, rename, environ
from sys import platform
from random import seed, uniform, shuffle
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
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau, Callback
from tensorflow.keras import backend as K
from tensorflow.keras.optimizers import Adam
import tensorflow_addons as tfa
from tools.l_tools import djconf
from tools.c_tools import cmetrics, hit100
from tools.c_logger import log_ini
from schools.c_schools import get_tagnamelist
from .models import trainframe, fit as sqlfit, epoch
from .hwcheck import getcputemp, getcpufan1, getcpufan2, getgputemp, getgpufan

global_load_model = None
global_tf = None

class sql_sequence(Sequence):
  def __init__(self, sqlresult, xdim, ydim, myschool, 
      normalisation=None,
      batch_size=32, 
      class_weights=None, 
      model=None,
      save_to_dir=None,
      save_prefix="",
      rotation_range=0,
      width_shift_range=0,
      height_shift_range=0,
      brightness_range=0,
      shear_range=0,
      zoom_range=None,
      horizontal_flip=False,
      vertical_flip=False,):
    self.sqlresult = sqlresult
    self.batch_size = batch_size
    self.xdim = xdim
    self.ydim = ydim
    self.normalisation = normalisation
    self.class_weights = class_weights
    self.model = model
    self.save_to_dir=save_to_dir
    self.save_prefix=save_prefix
    self.rotation_range=rotation_range
    self.width_shift_range=width_shift_range
    self.height_shift_range=height_shift_range
    self.brightness_range=brightness_range
    self.shear_range=shear_range
    self.zoom_range=zoom_range
    self.horizontal_flip=horizontal_flip
    self.vertical_flip=vertical_flip
    self.classes_list = get_tagnamelist(1)
    self.myschool = myschool

  def __len__(self):
    return ceil(len(self.sqlresult) / self.batch_size)

  def __getitem__(self, idx):
    batch_slice = self.sqlresult[idx*self.batch_size:(idx + 1)*self.batch_size]
    xdata = []
    ydata = np.empty(shape=(len(batch_slice), len(self.classes_list)))

    if (self.rotation_range or self.width_shift_range or self.height_shift_range 
      or self.shear_range or self.zoom_range):
      averages = []
    else:
      averages = None
    for i in range(len(batch_slice)):
      bmpdata = global_tf.io.read_file(batch_slice[i][1])
      bmpdata = global_tf.io.decode_bmp(bmpdata, channels=3)
      bmpdata = global_tf.image.resize(bmpdata, [self.xdim,self.ydim])
      if self.normalisation:
        bmpdata = global_tf.math.truediv(bmpdata, self.normalisation)
      if self.brightness_range > 0:
        bmpdata = global_tf.image.random_brightness(bmpdata, self.brightness_range)
      if self.normalisation:
        bmpdata = global_tf.clip_by_value(bmpdata, 0.00001, 255 / self.normalisation)
      else:
        bmpdata = global_tf.clip_by_value(bmpdata, 0.00001, 255)
      if averages is not None:
        average = global_tf.math.reduce_mean(bmpdata, (0, 1))
        average = [average] * self.ydim
        average = global_tf.stack(average)
        average = [average] * self.xdim
        average = global_tf.stack(average)
        averages.append(average)
      xdata.append(bmpdata)
      for j in range(len(self.classes_list)):
        ydata[i][j] = batch_slice[i][j+2]
    xdata = global_tf.stack(xdata)
    ydata = global_tf.convert_to_tensor(ydata)
    if averages is not None:
      averagedata = global_tf.stack(averages)
    else:
      averagedata = None

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

    if self.horizontal_flip:
      xdata = global_tf.image.random_flip_left_right(xdata)
    if self.vertical_flip:
      xdata = global_tf.image.random_flip_up_down(xdata)
    if self.rotation_range > 0:
      angles = [uniform(self.rotation_range*-1,self.rotation_range) * pi / 180 
        for x in range(len(batch_slice))]
      xdata = tfa.image.rotate(xdata, angles)
    if (self.width_shift_range > 0) or (self.height_shift_range > 0):
      matrixes = []
      for x in range(len(batch_slice)):
        xshift = uniform(self.width_shift_range*-1,
	        self.width_shift_range)*self.xdim
        yshift = uniform(self.height_shift_range*-1,
	        self.height_shift_range)*self.ydim
        matrix = [1,0,xshift,0,1,yshift,0,0]
        matrixes.append(matrix)
      matrixes = global_tf.convert_to_tensor(matrixes)
      xdata = tfa.image.transform(xdata, matrixes)
    if self.shear_range > 0:
      matrixes = []
      for x in range(len(batch_slice)):
        shear_lambda = self.shear_range / 45
        shear_lambda = uniform(shear_lambda*-1,shear_lambda)
        matrix = [1.0,shear_lambda,0,0,1.0,0,0,0]
        matrixes.append(matrix)
      matrixes = global_tf.convert_to_tensor(matrixes)
      xdata = tfa.image.transform(xdata, matrixes)
    if self.zoom_range is not None:
      matrixes = []
      for x in range(len(batch_slice)):
        xyfactor = 1/uniform(self.zoom_range[0],self.zoom_range[1])
        xshift = round(self.xdim * (1 / xyfactor - 1) * 0.5 * xyfactor)
        yshift = round(self.ydim * (1 / xyfactor - 1) * 0.5 * xyfactor)
        matrix = [xyfactor,0,xshift,0,xyfactor,yshift,0,0]
        matrixes.append(matrix)
      matrixes = global_tf.convert_to_tensor(matrixes)
      xdata = tfa.image.transform(xdata, matrixes)
    if averagedata is not None:
      xdata = global_tf.where(global_tf.equal(xdata, 0), averagedata, xdata)
    del averagedata

    if self.save_to_dir is not None:
      for i in range(len(batch_slice)):
        if self.normalisation:
          stored = global_tf.math.multiply(xdata[i], self.normalisation)
        else:
          stored = xdata[i]
        stored = global_tf.dtypes.cast(stored,global_tf.uint8)
        stored = global_tf.io.encode_jpeg(stored)
        print(self.save_to_dir+self.save_prefix+ts2filename(time())+'.jpg')
        global_tf.io.write_file(self.save_to_dir+self.save_prefix
	        +ts2filename(time())+'.jpg', stored)
        del stored

    if self.class_weights is None:
      return(xdata, ydata)
    else:
      return(xdata, ydata, wdata)

  def on_epoch_end(self):
    if self.class_weights is not None:
      shuffle(self.sqlresult)

class MyCallback(Callback):
  def __init__(self, myfit, logger):
    super().__init__()
    self.myfit = myfit
    self.logger = logger

  def on_epoch_begin(self, myepoch, logs=None):
    self.starttime = time()

  def on_epoch_end(self, myepoch, logs=None):
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
    sqlconnection.close()

def gpu_init(gpu_nr, gpu_mem_limit, logger):
  try:
    global global_load_model
    global global_tf
    environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
    environ["CUDA_VISIBLE_DEVICES"]=str(gpu_nr)
    import tensorflow as tf
    global_tf = tf
    if gpu_mem_limit:
      gpus = tf.config.list_physical_devices('GPU')
      for gpu in gpus:
        tf.config.set_logical_device_configuration(
            gpu, [tf.config.LogicalDeviceConfiguration(memory_limit=gpu_mem_limit)])
      logical_gpus = tf.config.list_logical_devices('GPU')
      logger.info(str(len(gpus))+" Physical GPUs, "+str(len(logical_gpus))+" Logical GPUs")
    from tensorflow.keras.models import load_model
    global_load_model = load_model
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
  val_split = djconf.getconfigfloat('validation_split', 0.33333333)
  mypatience = myschool.patience
  classes_list = get_tagnamelist(myschool.id)

  logger.info('*******************************************************************');
  logger.info('*** Working on School #'+str(myschool.id)+', '+myschool.name+'...');
  logger.info('*******************************************************************');

  templist = getlines(myschool, logger)
  trlist = templist['TR']
  valist = templist['VA']

  ts_start = timezone.now()

  myfit.made = ts_start
  myfit.nr_tr = len(trlist)
  myfit.nr_va = len(valist)
  myfit.status = "Working"
  myfit.save(update_fields=["made", "nr_tr", "nr_va", "status"])

  weightarray = [0] * (len(classes_list) + 1)

  if sqlfit.objects.filter(school=myschool.id).exists():
	  fitnr = sqlfit.objects.filter(school=myschool.id).latest('id').id
  else:
	  fitnr = -1
  model_name = myschool.model_type
  if path.exists(myschool.dir+'model/'+model_name+'.h5'):
    copyfile(myschool.dir+'model/'+model_name+'.h5', myschool.dir+'model/'+model_name+'_'+str(fitnr)+'.h5')
    model_to_load = myschool.id
  else:
    model_to_load = 1
  logger.info('*** Loading model '+myschool.dir+'...');
  model = global_load_model(myschool.dir+'model/'+model_name+'.h5', 
    custom_objects={'cmetrics': cmetrics, 'hit100': hit100,})
  xdim = model.layers[0].input_shape[1]
  ydim = model.layers[0].input_shape[2]
  description = "min. l_rate: " + myschool.l_rate_min
  description += "  max. l_rate: " + myschool.l_rate_max 
  description += "  patience: " + str(mypatience) + "\n" 
  description += "weight_max: " + str(myschool.weight_max)
  description += "  weight_min: " + str(myschool.weight_max) 
  description += "  weight_boost: " + str(myschool.weight_boost) + "\n" 
  l_rate = model.optimizer.learning_rate.numpy()
  logger.info('>>> Learning rate from the model: '+str(l_rate))
  l_rate = max(l_rate, float(myschool.l_rate_min))
  if float(myschool.l_rate_max) > 0:
    l_rate = min(l_rate, float(myschool.l_rate_max))
  logger.info('>>> New learning rate: '+str(l_rate))
  K.set_value(model.optimizer.learning_rate, l_rate)
  model.compile(loss='binary_crossentropy',
	  optimizer=Adam(learning_rate=l_rate),
	  metrics=[hit100, cmetrics])
  #stringlist = []
  #model.summary(print_fn=lambda x: stringlist.append(x))
  #short_model_summary = "\n".join(stringlist)
  #description += short_model_summary
  for item in trlist:
	  found_class = False
	  for count in range(len(classes_list)):
		  if item[count+2] >= 0.5:
			  weightarray[count] += 1
			  found_class = True
	  if (not found_class):
		  weightarray[len(classes_list)] += 1

  class_weights = [myschool.weight_max - ((x * (myschool.weight_max - myschool.weight_min)) / max(weightarray)) for x in weightarray]
  description += '*** Weight Configuration ***\n' 
  for i in range(len(classes_list)):
    description += (classes_list[i] + ' - ' +  str(weightarray[i]) + ' - ' + str(class_weights[i])) + "\n" 
  description += ('none - ' +  str(weightarray[-1]) + ' - ' + str(class_weights[-1])) + "\n" 

  train_sequence = sql_sequence(trlist, xdim, ydim, myschool,
    normalisation = None,
    batch_size=batchsize, 
    class_weights=class_weights, 
    model=model,
    #save_to_dir='/home/ludger/temp/',
    #save_prefix='test'
    rotation_range=5,
    width_shift_range=0.2,
    height_shift_range=0.2,
    brightness_range=0.5,
    shear_range=0.2,
    zoom_range=(0.75, 1.25),
    horizontal_flip=True,
    vertical_flip=False,
  )

  description += """
*** Image Augmentation ***
train_sequence = sql_sequence(trlist, xdim, ydim, myschool,
  normalisation = None,
  batch_size=batchsize, 
  class_weights=class_weights, 
  model=model,
  #save_to_dir='/home/ludger/temp/',
  #save_prefix='test',
  rotation_range=5,
  width_shift_range=0.2,
  height_shift_range=0.2,
  brightness_range=0.5,
  shear_range=0.2,
  zoom_range=(0.75, 1.25),
  horizontal_flip=True,
  vertical_flip=False,)
"""
  logger.info(description)

  vali_sequence = sql_sequence(valist, xdim, ydim, myschool,
	  batch_size=batchsize)

  es = EarlyStopping(monitor='val_loss', mode='min', verbose=0,
    min_delta=0.00001, patience=mypatience)
  mc = ModelCheckpoint(myschool.dir+'model/'+model_name+'_temp.h5', 
	  monitor='val_loss', mode='min', verbose=0, save_best_only=True)
  reduce_lr = ReduceLROnPlateau(monitor='val_loss', mode='min', factor=sqrt(0.1),
	  patience=3, min_lr=0.0000001, min_delta=0.00001, verbose=0)
  cb = MyCallback(myfit, logger)

  sqlconnection.close()

  history = model.fit(
	  x=train_sequence,
	  validation_data=vali_sequence,
    shuffle=False,
	  epochs=epochs, 
	  verbose=0,
	  callbacks=[es, mc, reduce_lr, cb,],
	  #use_multiprocessing=True,
	  )
  cputemp = getcputemp()
  cpufan1 = getcpufan1()
  cpufan2 = getcpufan2()
  if cpufan2 is None:
	  cpufan2 = 0
  gputemp = getgputemp(1)
  if gputemp is None:
	  gputemp = 0
  gpufan = getgpufan(1)
  if gpufan is None:
	  gpufan = 0

  if (platform.startswith('win') 
		  and path.exists(myschool.dir+'model/'+model_name+'.h5')):
	  remove(myschool.dir+'model/'+model_name+'.h5')
  rename(myschool.dir+'model/'+model_name+'_temp.h5', 
	  myschool.dir+'model/'+model_name+'.h5')
  model = global_load_model(myschool.dir+'model/'+model_name+'.h5', 
	  custom_objects={'cmetrics': cmetrics,
		  'hit100': hit100,})

  myschool.lastmodelfile = timezone.now()
  myschool.save(update_fields=["lastmodelfile"])

  if len(history.history['loss'])	>= epochs:
	  mypatience = 0
  epochs = len(history.history['loss'])	
  if epochs < mypatience + 1:
	  mypatience = epochs - 1 
  myfit.minutes = (timezone.now()-ts_start).total_seconds() / 60
  myfit.epochs = epochs
  myfit.loss = float(history.history['loss'][epochs-mypatience-1])
  myfit.cmetrics = float(history.history['cmetrics'][epochs-mypatience-1])
  myfit.hit100 = float(history.history['hit100'][epochs-mypatience-1])
  myfit.val_loss = float(history.history['val_loss'][epochs-mypatience-1])
  myfit.val_cmetrics = float(history.history['val_cmetrics'][epochs-mypatience-1])
  myfit.val_hit100 = float(history.history['val_hit100'][epochs-mypatience-1])
  myfit.cputemp = cputemp
  myfit.cpufan1 = cpufan1
  myfit.cpufan2 = cpufan2
  myfit.gputemp = gputemp
  myfit.gpufan = gpufan
  myfit.status = 'Done'
  myfit.description = description
  myfit.save(update_fields=[
    "minutes", "epochs", "loss", "cmetrics", "hit100", 
    "val_loss", "val_cmetrics", "val_hit100", "cputemp", "cpufan1", 
    "cpufan2", "gputemp", "gpufan", "status", "description", ])

  logger.info('***  Done  ***')
