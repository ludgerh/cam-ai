from sys import argv
from tools.c_redis import myredis
from time import sleep

print('*** CAM-AI server running ***')
print('Calling:', argv)
redis = myredis()
redis.set_watch_status(2)
while(redis.get_watch_status()):
  if redis.get_watch_status() == 2:
    redis.set_watch_status(1)
    print(int(redis.get_watch_status()))
    ### Programm starten
  sleep(10.0)
  print('nix zu tun')
    
