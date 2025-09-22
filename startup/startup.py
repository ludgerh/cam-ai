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
import os
from glob import glob
from signal import signal, SIGINT
from multiprocessing import Lock as p_lock
from .redis import my_redis as startup_redis
from tools.l_tools import djconf, kill_all_processes
from tools.l_break import a_break_type, a_break_time, BR_LONG
from tools.health import my_health_runner
from cleanup.c_cleanup import my_cleanup

#from threading import enumerate

glob_startup = None
    

class startup_class(): 

  async def run(self):
    from logging import getLogger
    from asgiref.sync import sync_to_async
    from tools.c_logger import alog_ini
    from tools.version_upgrade import version_upgrade
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
    from camai.c_settings import safe_import
    data_path = safe_import('data_path') 
    db_database = safe_import('db_database') 
    from trainers.c_trainers import clean_fits
    from django.apps import apps
    try:
      while not apps.ready:
        await a_break_type(BR_LONG)
      for path in glob("/dev/shm/psm_*"):
        try:
          os.remove(path)
        except FileNotFoundError:
          pass  # falls inzwischen schon weg
        except PermissionError as e:
          print("No privileges to remove:", path, e)
      for path in glob("shm/cam*.pipe"):
        try:
          os.remove(path)
        except FileNotFoundError:
          pass  # falls inzwischen schon weg
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
      startup_redis.set_start_trainer_busy(0)
      startup_redis.set_start_worker_busy(0)
      startup_redis.set_start_stream_busy(0)
      startup_redis.set_shutdown_command(0)
      await sync_to_async(version_upgrade)(old_version, software_version)
      await clean_fits()
      for item in tf_workers:
        tf_workers[item].start()
      for item in trainers:
        trainers[item].start()
      for item in viewables:
        await viewables[item]['stream'].run()
      asyncio.create_task(self.restartcheck_thread())
      asyncio.create_task(my_health_runner.health_task())  
      self.cleanup = my_cleanup
      self.cleanup.run()  
      while self.do_run:  
        await asyncio.sleep(1.0)
    except:
      from traceback import format_exc
      logger.error('Error in process: ' + logname)
      logger.error(format_exc())  
      kill_all_processes()

  async def restartcheck_thread(self):
    from globals.c_globals import trainers, tf_workers, viewables
    from streams.c_streams import c_stream
    from streams.models import stream
    from tf_workers.c_tf_workers import tf_worker
    from trainers.c_trainers import trainer
    while self.do_run:
      if (startup_redis.get_shutdown_command() in {10, 20}):
        os.kill(os.getpid(), SIGINT)
        return() 
      if (item := startup_redis.get_start_trainer_busy()):
        if (item in trainers):
          trainers[item].stop()
        glob_lock = p_lock()
        my_worker = tf_workers[1] #may be variable in the future 
        trainers[item] = trainer(
          item, 
          my_worker.inqueue,
          my_worker.registerqueue,
          glob_lock,
        )
        trainers[item].start()
        startup_redis.set_start_trainer_busy(0)
      if (item := startup_redis.get_start_worker_busy()):
        if (item in tf_workers):
          tf_workers[item].stop()
        tf_workers[item] = tf_worker(item)
        tf_workers[item].start()
        startup_redis.set_start_worker_busy(0)
      if (item := startup_redis.get_start_stream_busy()):
        if item in viewables:
          await viewables[item]['stream'].stop()
        else:
          viewables[item] = {} 
        viewables[item]['stream'] = c_stream(item)
        await viewables[item]['stream'].run()
        startup_redis.set_start_stream_busy(0)  
      await a_break_time(10.0)  
    
    
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
  my_health_runner.stop()
  glob_startup.cleanup.stop()
  for i in viewables:
    print('Closing stream #', i)
    await viewables[i]['stream'].stop()
  for i in tf_workers:
    print('Closing tf_worker #', i)
    await tf_workers[i].stop()
  for i in trainers:
    print('Closing trainer #', i)
    await trainers[i].stop() 
  kill_all_processes()
  exit(0) 
    
def handle_signal(signum, frame):
  try:
      loop = asyncio.get_running_loop()
      loop.create_task(newexit())
  except RuntimeError:
      asyncio.run(newexit())
  
