"""
Copyright (C) 2024-2026 by the CAM-AI team, info@cam-ai.de
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

import subprocess
import os
import sys
from datetime import datetime
from sys import argv
from signal import signal, SIGINT, SIGTERM, SIGHUP
from time import sleep, time
from sysinfo import sysinfo

ctrl_c_count = 2
ts = 0
first_round = True

def sigint_handler(signal, frame):
  global ctrl_c_count
  global ts
  if ctrl_c_count == 2:
    ts = time()
  else:
    if time() - ts > 1.0:
      ctrl_c_count = 2
      ts = time()
  if ctrl_c_count:
    ctrl_c_count -= 1
  else: 
    print('Killing cam-ai-server.py...')    
    sys.exit(0)
    
def call_in_env(cmd, sys_info):
  if sys_info['hw'] == 'raspi':
    cmd_list = 'source ~/miniforge3/etc/profile.d/conda.sh; '
  if sys_info['hw'] == 'pc':
    cmd_list = 'source ~/miniconda3/etc/profile.d/conda.sh; '
  cmd_list += 'conda activate tf; '
  cmd_list += cmd + '; '  
  print('Called in Env:', cmd_list)
  subprocess.call(cmd_list, shell=True, executable='/bin/bash')
     

if argv[1] == 'nvidia':
  use_nvidia = True
  call_pars = argv[1:]
else:
  use_nvidia = False
  call_pars = argv   
my_sysinfo = sysinfo()
print(my_sysinfo)
if len(call_pars) > 1:
  from setproctitle import setproctitle
  from startup.redis import my_redis as startup_redis
  setproctitle('CAM-AI-Server')
  signal(SIGINT, sigint_handler)
  signal(SIGTERM, sigint_handler)
  signal(SIGHUP, sigint_handler)
  print('***** CAM-AI server is running *****')
  print('Calling: python ' + ' '.join(call_pars[1:]))
  print()
  startup_redis.set_shutdown_command(0) 
  while True:
    call_pars[0] = 'python'
    
    
    
    call_in_env('pip install --upgrade pip', my_sysinfo)
    if use_nvidia:
      cmd = 'pip install -r requirements.nvidia_' 
    else:
      cmd = 'pip install -r requirements.' + my_sysinfo['hw'] + '_' 
    cmd += my_sysinfo['dist_version']
    call_in_env(cmd, my_sysinfo)
    if first_round:
      if os.path.exists('last_run.dat') or os.path.exists('data'):
        # This can be removed as soon as everybody has 2.0.3 installed
        cmd = ('python manage.py migrate tf_workers '
          + '0001_squashed_0058_auto_20260117_1253 --fake')
        call_in_env(cmd, my_sysinfo)
        cmd = ('python manage.py migrate cleanup '
          + '0001_squashed_0011_remove_status_line_event_stream_and_more --fake')
        call_in_env(cmd, my_sysinfo)
        cmd = ('python manage.py migrate eventers '
          + '0001_squashed_0015_event_deleted_event_frame_deleted --fake')
        call_in_env(cmd, my_sysinfo)
        cmd = ('python manage.py migrate streams '
          + '0001_squashed_0030_stream_eve_one_frame_per_event --fake')
        call_in_env(cmd, my_sysinfo)
        cmd = ('python manage.py migrate trainers '
          + '0001_squashed_0042_auto_20260117_1413 --fake')
        call_in_env(cmd, my_sysinfo)
      else:  
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("last_run.dat", "w", encoding="utf-8") as f:
            f.write(now + "\n")
      first_round = False
    call_in_env('python manage.py migrate', my_sysinfo)
    subprocess.call(call_pars)
    if startup_redis.get_shutdown_command() in {0, 10, 11}:
      break
    else: 
      sleep(0.1) 
  if startup_redis.get_shutdown_command() == 10:  
    os.system('sudo shutdown now') 
  if startup_redis.get_shutdown_command() == 11:  
    os.system('sudo reboot now') 
  print('***** CAM-AI server is done *****')  
    
