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

import sys
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from redis import Redis
from multitimer import MultiTimer
from tools.l_tools import djconf
from camai.version import version as software_version
print('***** Software-Version: ', software_version, '*****')
djconf.setconfig('version', software_version)
from tf_workers.models import worker
from tf_workers.c_tfworkers import tf_workers, tf_worker
from trainers.models import trainer as trainerdb
from trainers.c_trainers import trainers, trainer
from .models import stream
from .c_streams import streams, c_stream
#from threading import enumerate

check_timer = None
start_worker_list = set()
start_stream_list = set()

def restartcheck_proc():
  global start_worker_list
  global start_stream_list
  if start_worker_list:
    for i in start_worker_list:
      dbline = worker.objects.get(id=i)
      tf_workers[dbline.id] = tf_worker(dbline.id)
      tf_workers[dbline.id].run()
    start_worker_list = set()
  if start_stream_list:
    for i in start_stream_list:
      dbline = stream.objects.get(id=i)
      streams[i] = c_stream(dbline)
      streams[i].start()
    start_stream_list = set()
    

def newexit(eins, zwei):
  check_timer.stop()
  print ('Caught KeyboardInterrupt...')
  for i in streams:
    print('Closing stream #', i)
    streams[i].stop()
  for i in tf_workers:
    print('Closing tf_worker #', i)
    tf_workers[i].stop()
  for i in trainers:
    print('Closing trainer #', i)
    trainers[i].stop()
  #for thread in enumerate(): 
  #  print(thread)
  sys.exit()


def run():
  global check_timer
  signal(SIGINT, newexit)
  signal(SIGTERM, newexit)
  signal(SIGHUP, newexit)

  setproctitle('CAM-AI-Starter')

  myredis = Redis(health_check_interval=30)
  myredis.set('camai_number_postprocesses', 0)

  for dbline in trainerdb.objects.filter(active=True):
    trainers[dbline.id] = trainer(dbline.id)
    trainers[dbline.id].run()

  for dbline in worker.objects.filter(active=True):
    tf_workers[dbline.id] = tf_worker(dbline.id)
    tf_workers[dbline.id].run()
  
  for dbline in stream.objects.filter(active=True):
    streams[dbline.id] = c_stream(dbline)
    streams[dbline.id].start()

  check_timer = MultiTimer(interval=10, function=restartcheck_proc, runonstart=False)
  check_timer.start()

