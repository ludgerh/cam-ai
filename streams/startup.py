import sys
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from redis import Redis
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

def newexit(eins, zwei):
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

