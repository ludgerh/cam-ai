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

import asyncio
import aiofiles.os
import numpy as np
from os import path, getpid, scandir
from threading import Thread
from queue import Queue, Empty
from subprocess import Popen
from datetime import datetime
from psutil import Process
from django.db import connection
from django.db.utils import OperationalError
from .models import setting

logdict = {
  'NOTSET' : 0,
  'DEBUG' : 10,
  'INFO' : 20,
  'WARNING' : 30,
  'ERROR' : 40,
  'CRITICAL' : 50,
}

def str_to_bool(instring):
  if instring in ('1', 'true', 'True', 'yes', 'Yes', 'ja', 'Ja'):
    return(True)
  elif instring in ('0', 'false', 'False', 'no', 'No', 'nein', 'Nein'):
    return(False)
  else:
    return(None)

def bool_to_string(inbool):
  if inbool:
    return('1')
  else:
    return('0')

class djconfig():
  def __init__(self, rediscache = False):
    self.redis = rediscache
    if self.redis:
      from redis import Redis
      self.myredis = Redis(health_check_interval=30)
      for item in setting.objects.all():
        self.mycache[item.setting] = item.value
        self.myredis.set('djconfig:'+item.setting, item.value)
    else:
      self.mycache = {}
      for item in setting.objects.all():
        self.mycache[item.setting] = item.value
        
  def setconfig(self, param, value):
    try:
      line = setting.objects.get(setting=param)
      line.value = value
    except setting.DoesNotExist:
      line = setting(setting=param, value=value, comment='No Comment')
    if self.redis:
      self.myredis.set('djconfig:'+param, value)
    else:
      self.mycache[param] = value
    line.save()

  def getconfig(self, param, default=None, forcedb=False):
    if self.redis:
      if (not forcedb) and (value := self.myredis.get('djconfig:'+param)):
        return(value.decode())
    else:
      if (not forcedb) and (param in self.mycache):
        return(self.mycache[param])
    try:
      while True:
        try:
          line = setting.objects.get(setting=param)
          break
        except OperationalError:
          connection.close()
      result = line.value
    except setting.DoesNotExist:
      result = default
    if self.redis:
      self.myredis.set('djconfig:'+param, result)
    else:
      self.mycache[param] = result
    return(result)

  def delconfig(self, param): 
    setting.objects.filter(setting=param).delete()
    if self.redis:
      self.myredis.delete('djconfig:'+param)
    else:
      del self.mycache[param]

  def setconfigint(self, param, value):
    self.setconfig(param, str(value))

  def getconfigint(self, param, default=None, forcedb=False):
    temp = self.getconfig(param, forcedb=forcedb)
    if temp is None:
      return(default)
    else:
      return(int(temp))

  def setconfigfloat(self, param, value):
    self.setconfig(param, str(value))

  def getconfigfloat(self, param, default=None, forcedb=False):
    temp = self.getconfig(param)
    if temp is None:
      return(default)
    else:
      return(float(temp))

  def setconfigbool(self, param, value):
    self.setconfig(param, str(value))

  def getconfigbool(self, param, default=None, forcedb=False):
    if type(default) == bool:
      default = bool_to_string(default) 
    temp = self.getconfig(param, default)
    if temp:
      if temp in ('1', 'true', 'True', 'yes', 'Yes', 'ja', 'Ja'): 
	      return(True)
      elif temp in ('0', 'false', 'False', 'no', 'No', 'nein', 'Nein'): 
	      return(False)
      else:
	      return(None)
    else:
      return(default)

djconf = djconfig()

def ts2filename(rein, noblank=False) :
  if noblank:
    return(datetime.fromtimestamp(rein).strftime('%Y-%m-%d-%H-%M-%S-%f'))
  else:
    return(datetime.fromtimestamp(rein).strftime('%Y-%m-%d %H-%M-%S-%f'))

def ts2mysqltime(rein) :
  return(datetime.fromtimestamp(rein).strftime('%H:%M:%S'))

class QueueUnknownKeyword(Exception):
  def __init__(self, keyword, message="Unknown keyword: "):
    self.message = message + keyword
    super().__init__(self.message)

def uniquename(pathname, filename, extension):
#filename goes into result string, pathname does not
  stemp = filename
  counter = 0
  while path.exists(pathname+filename+'.'+extension):
    filename = stemp+'-'+str(counter)
    counter = counter+1
  return(filename+'.'+extension)

async def uniquename_async(pathname, filename, extension):
#filename goes into result string, pathname does not
  stemp = filename
  counter = 0
  while await aiofiles.os.path.exists(pathname+filename+'.'+extension):
    filename = stemp+'-'+str(counter)
    counter = counter+1
  return(filename+'.'+extension)

def randomfilter(outlength, *args):
  arglist = list(args)
  if len(arglist[0]) > outlength:
    randIndex = sample(range(len(args[0])), outlength)
    randIndex.sort()
    for i in range(len(arglist)):
      if type(arglist[i]) is list:
        arglist[i] = [arglist[i][j] for j in randIndex]
      elif isinstance(arglist[i], np.ndarray):
        print('+++', arglist[i].shape[0])
        print('!!!', len(randIndex))
        output = np.empty((0, arglist[i].shape[1]), arglist[i].dtype)
        for j in randIndex:
          if j < arglist[i].shape[0]:
            print(output.shape, arglist[i].shape)
            output = np.vstack((output, arglist[i][j]))
        arglist[i] = output
        print('---', arglist[i].shape[0])
  return(arglist)

def np_mov_avg(input, radius):
  if (radius == 0) or (input.shape[0] <= 1):
    return(input)
  else:
    result = []
    for i in range(input.shape[0]):
      segment = np.average(input[max(0, i-radius):min(input.shape[0], i+radius+1)], axis=0)
      result.append(segment)
    result = np.stack(result)
    return(result)

class popenplus():
  def __init__(self, onExit, *popenArgs, **popenKWArgs):
    thread = Thread(target=self.runInThread, args=(onExit, popenArgs, popenKWArgs))
    thread.start()

  def runInThread(self, onExit, popenArgs, popenKWArgs):
    self.proc = Popen(*popenArgs, **popenKWArgs)
    self.proc.wait()
    self.proc = None
    onExit()

  def stop(self):
    if self.proc:
      self.proc.kill()

def get_proc_name():
  return(Process(getpid()).name())

class NonBlockingStreamReader:

  def __init__(self, stream, packet_size=0):
    #stream: the stream to read from. Usually a process stdout or stderr.
    #packet_size: Size of read chunks, 0 --> readline is used

    self._s = stream
    self._q = Queue()
    self._ps = packet_size
    self._dorun = True

    def _populateQueue(stream, queue):
      while self._dorun:
        if self._ps:
          chunk = stream.read(self._ps)
        else:
          chunk = stream.readline()
        if chunk:
          queue.put(chunk)
        else:
          #print('***** EndOfStream')
          break

    self._t = Thread(target = _populateQueue,
      args = (self._s, self._q))
    self._t.daemon = True
    self._t.start() #start collecting lines from the stream

  def readchunk(self, timeout = None):
    try:
      return self._q.get(block = timeout is not None,
              timeout = timeout)
    except Empty:
      return None

  def stop(self):
    self._dorun = False

def seq_to_int(in_seq):
  result = 0
  for i in range(len(in_seq)):
    if in_seq[i]:
      result += 1 << i
  return(result) 

def displaybytes(numberin):
  stringout = 'B'
  result = float(numberin)
  if abs(result) >= 100.0:
    result /= 1000.0
    stringout = 'K'
  if abs(result) >= 100.0:
    result /= 1000.0
    stringout = 'M'
  if abs(result) >= 100.0:
    result /= 1000.0
    stringout = 'G'
  if abs(result) >= 100.0:
    result /= 1000.0
    stringout = 'T'
  return(str(round(result, 3))+stringout)

class async_timer:
  def __init__(self, timeout, callback):
    self._timeout = timeout
    self._callback = callback
    self._task = asyncio.ensure_future(self._job())

  async def _job(self):
    await asyncio.sleep(self._timeout)
    await self._callback()

  def cancel(self):
    self._task.cancel()
    
def version_flat(string_in):
  result = 0
  for item in string_in.split('.'):
    if item[-1].isalpha():
      result += int(item[:-1])
      letter_nr = ord(item[-1].lower())
    else:  
      result += int(item)
      letter_nr = 0
    result *= 100000
  result += letter_nr
  return(result)
  
def version_full(int_in):
  last = True
  temp = int_in % 100000
  if temp:
    result = chr(temp)
  else:
    result = ''
  int_in //= 100000  
  while int_in:  
    if last:
      last = False
    else:  
      result = '.' + result
    result = str(int_in % 100000) + result 
    int_in //= 100000 
  return(result)  
  
def get_dir_size(path='.'):
  total = 0
  try:
    with scandir(path) as it:
      for entry in it:
        if entry.is_file():
          total += entry.stat().st_size
        elif entry.is_dir():
          total += get_dir_size(entry.path)
  except FileNotFoundError:
    total = 0        
  return total

