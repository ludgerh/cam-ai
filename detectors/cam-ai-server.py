import subprocess
import os
from sys import argv
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from tools.c_redis import myredis
from time import sleep

def sigint_handler(signal, frame):
  #print ('Devices: Interrupt is caught')
  pass

setproctitle('CAM-AI-Server')
signal(SIGINT, sigint_handler)
signal(SIGTERM, sigint_handler)
signal(SIGHUP, sigint_handler)
basepath = os.getcwd() 
print('***** CAM-AI server is running *****')
print('Calling: python ' + ' '.join(argv[1:]))
print()
redis = myredis()
redis.set_watch_status(2)
while(redis.get_watch_status()):
  if redis.get_watch_status() == 2:
    redis.set_watch_status(1)
    call_pars = argv
    call_pars[0] = 'python'
    os.chdir(basepath)
    subprocess.call(call_pars) 
  sleep(10.0)
print('***** CAM-AI server is done *****')  
    
