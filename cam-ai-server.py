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

import subprocess
import os
import sys
from sys import argv
from signal import signal, SIGINT, SIGTERM, SIGHUP
from setproctitle import setproctitle
from startup.redis import my_redis as startup_redis
from time import sleep, time

ctrl_c_count = 2
ts = 0

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
    print('Killing cam-ai-ser.py...')    
    sys.exit(0)


setproctitle('CAM-AI-Server')
signal(SIGINT, sigint_handler)
signal(SIGTERM, sigint_handler)
signal(SIGHUP, sigint_handler)
basepath = os.getcwd() 
print('***** CAM-AI server is running *****')
print('Calling: python ' + ' '.join(argv[1:]))
print()
startup_redis.set_shutdown_command(0) 
while True:
  call_pars = argv
  call_pars[0] = 'python'
  os.chdir(basepath)
  subprocess.call(call_pars)
  if startup_redis.get_shutdown_command() in {0, 10}:
    break
if startup_redis.get_shutdown_command() == 10:   
  os.system('sudo shutdown now') 
print('***** CAM-AI server is done *****')  
    
