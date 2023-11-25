import subprocess
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
print('*** CAM-AI server running ***')
print('Calling: python ' + ' '.join(argv[1:]))
redis = myredis()
redis.set_watch_status(2)
while(redis.get_watch_status()):
  if redis.get_watch_status() == 2:
    redis.set_watch_status(1)
    print(int(redis.get_watch_status()))
    call_pars = argv
    call_pars[0] = 'python'
    print(call_pars)
    subprocess.call(call_pars) 
  sleep(10.0)
  print('nix zu tun')
print('finished')  
    
