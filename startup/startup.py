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


import asyncio
from signal import signal, SIGINT
from .redis import my_redis as startup_redis
from tools.l_tools import djconf, kill_all_processes
#from django.apps import apps as django_apps
#from time import sleep
#import os
#from traceback import format_exc
#from aiomultiprocess import set_start_method
#from camai.c_settings import safe_import
#import schools.c_schools
#from tf_workers.c_tfworkers import tf_workers
#from tools.health import stop as stophealth
#from tools.version_upgrade import version_upgrade
#from cleanup.c_cleanup import my_cleanup, c_cleanup
#from streams.c_streams import streams
#data_path = safe_import('data_path') 
#db_database = safe_import('db_database') 

#from threading import enumerate

glob_startup = None
    

class startup_class(): 

  async def run(self):
    from logging import getLogger
    from asgiref.sync import sync_to_async
    from tools.c_logger import alog_ini
    from tools.version_upgrade import version_upgrade
    from cleanup.c_cleanup import c_cleanup
    from camai.db_ini import db_ini
    from camai.version import version as software_version
    from camai.passwords import (
      smtp_account,
      smtp_password,
      smtp_server,
      smtp_port,
      smtp_email,
    )
    from globals.c_globals import trainers, tf_workers, viewables
    from tools.l_break import a_break_type, BR_LONG
    from camai.c_settings import safe_import
    data_path = safe_import('data_path') 
    db_database = safe_import('db_database') 
    from trainers.c_trainers import clean_fits
    from django.apps import apps
    try:
      while not apps.ready:
        await a_break_type(BR_LONG)
      logname = 'startup'
      logger = getLogger(logname)
      await alog_ini(logger, logname)
      self.do_run = True
      await db_ini()
      print('***** Software-Version: ', software_version, '*****')
      old_version = await djconf.agetconfig('version', '0.0.0')
      await djconf.asetconfig('version', software_version)
      print('***** DataPath: ', data_path, '*****')
      await djconf.asetconfig('datapath', data_path)
      print('***** Database: ', db_database, '*****')
      await djconf.asetconfig('smtp_account', smtp_account)
      await djconf.asetconfig('smtp_password', smtp_password)
      await djconf.asetconfig('smtp_server', smtp_server)
      await djconf.asetconfigint('smtp_port', smtp_port)
      await djconf.asetconfig('smtp_email', smtp_email)
      self.restart_mode = 0
      startup_redis.set_start_trainer_busy(0)
      startup_redis.set_start_worker_busy(0)
      startup_redis.set_start_stream_busy(0)
      startup_redis.set_shutdown_command(0)
      await sync_to_async(version_upgrade)(old_version, software_version)
      await clean_fits()
      for item in trainers:
        trainers[item].start()
      for item in tf_workers:
        tf_workers[item].start()
      for item in viewables:
        await viewables[item]['stream'].run()
      while self.do_run:  
        await asyncio.sleep(1.0)
      return()  
      self.cleanup = c_cleanup()
      my_cleanup.run()  
      check_thread = Thread(target = restartcheck_thread, name='RestartCheckThread').start()
    except:
      from traceback import format_exc
      logger.error('Error in process: ' + logname)
      logger.error(format_exc())  
      kill_all_processes()

def restartcheck_thread():
  from streams.c_streams import c_stream
  from streams.models import stream
  from tf_workers.c_tfworkers import tf_worker
  from trainers.c_trainers import trainer
  global restart_mode
  while do_run:
    if (command := startup_redis.get_shutdown_command()):
      startup_redis.set_shutdown_command(0)
      if command == 1:
        restart_mode = 1
      elif command == 2:  
        restart_mode = 2
      os.kill(os.getpid(), SIGINT)
      return()
    if (item := startup_redis.get_start_trainer_busy()):
      if (item in trainers) and trainers[item].do_run:
        trainers[item].stop()
      trainers[item] = trainer(item)
      trainers[item].run()
      startup_redis.set_start_trainer_busy(0)
    if (item := startup_redis.get_start_worker_busy()):
      if (item in tf_workers) and tf_workers[item].do_run:
        tf_workers[item].stop()
      tf_workers[item] = tf_worker(item)
      tf_workers[item].run()
      startup_redis.set_start_worker_busy(0)
    if (item := startup_redis.get_start_stream_busy()):
      dbline = stream.objects.get(id=item)
      if item in viewables:
        viewables[item]['stream'].stop()
      viewables[item]['stream'] = c_stream(dbline)
      viewables[item]['stream'].start()
      startup_redis.set_start_stream_busy(0)    
    sleep(10.0)
    
    
def launch():
        
  def startup_thread():
    loop = asyncio.new_event_loop() 
    asyncio.set_event_loop(loop)  
    loop.run_until_complete(glob_startup.run())
    loop.close() 
    
  from threading import Thread
  global glob_startup
  glob_startup = startup_class()
  signal(SIGINT, handle_signal)
  if startup_redis.get_running():
    print('Startup.Launch: Return because busy')
    return()
  startup_redis.set_running(True) 
  thread = Thread(target=startup_thread)
  thread.start()
    
async def newexit():
  from globals.c_globals import trainers, tf_workers, viewables
  global glob_startup
  startup_redis.set_running(False) 
  print ('Caught KeyboardInterrupt...')
  glob_startup.do_run = False
  #sleep(5.0)
  #stophealth()
  #my_cleanup.stop()
  for i in viewables:
    print('Closing stream #', i)
    await viewables[i]['stream'].stop()
  for i in tf_workers:
    print('Closing tf_worker #', i)
    await tf_workers[i].stop()
  for i in trainers:
    print('Closing trainer #', i)
    await trainers[i].stop()  
  if glob_startup.restart_mode == 0:
    startup_redis.set_watch_status(0) 
    #for thread in enumerate(): 
    #  print(thread)
    kill_all_processes()
  elif startup.restart_mode == 1:
    startup_redis.set_watch_status(0) 
    #for thread in enumerate(): 
    #  print(thread)
    os.system('sudo shutdown now')
    kill_all_processes()
  elif startup.restart_mode == 2:
    startup_redis.set_watch_status(2) 
    #for thread in enumerate(): 
    #  print(thread)
  exit(0) 
    
def handle_signal(signum, frame):
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(newexit())
    except RuntimeError:
        asyncio.run(newexit())
  
