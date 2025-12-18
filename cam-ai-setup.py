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
import requests
import json
import pathlib
import re
import sys
import shlex
from time import sleep
from shutil import move, rmtree, copy
from zipfile import ZipFile
from glob import glob
from getpass import getpass
import platform

run_all = True

def cpuinfo():
  with open("/proc/cpuinfo", "r") as f:
    cpuinfo = f.read().splitlines()
  result = {}  
  processor = None
  for line in cpuinfo:
    if line:
      list = line.split(':')
      list = [list[0].strip(), list[1].strip()]
      if list[0] == 'processor':
        processor = list[1]
        result[processor] = {}
      if processor:
        result[processor][list[0]] = list[1]
      else:  
        result[list[0]] = list[1]
    else:
      processor = None
  return(result)   

def meminfo():
  with open("/proc/meminfo", "r") as f:
    meminfo = f.read().splitlines()
  result = {}  
  for line in meminfo:
    if line:
      list = line.split(':')
      list = [list[0].strip(), list[1].strip()]
      if list[0] == 'MemTotal':
        templist = list[1].split()[0]
        result['total'] = round(float(list[1].split()[0]) / 1000000.0)
  return(result)  
  
def osinfo():
  result = platform.freedesktop_os_release()
  return(result) 
  
def sysinfo():
  result = {}
  cpu = cpuinfo()
  if 'Model' in cpu and cpu['Model'][:12] == 'Raspberry Pi':   
    result['hw'] = 'raspi'
    result['hw_version'] = cpu['Model'].split()[2]
  else:     
    result['hw'] = 'pc'
    result['hw_version'] = cpu['0']['cpu family'] 
  mem = meminfo()
  result['hw_ram'] = mem['total']
  myos = platform.freedesktop_os_release()
  result['dist'] = myos['ID']
  result['dist_version'] = myos['VERSION_ID']
  return(result) 

installdir = 'cam-ai'
db_pass = None

def sql_query(command):
  subprocess.call(['mariadb', '-u', 'root', '-p'+db_pass, '-e', command]) 
  
def sh(cmd, **kwargs):
  return subprocess.run(shlex.split(cmd), check=True, **kwargs)

def write_root_file(path, content, mode="0644"):
  sh(f"sudo install -d -m 0755 $(dirname {shlex.quote(path)})")
  p = subprocess.Popen(["sudo", "tee", path], stdin=subprocess.PIPE)
  p.communicate(input=content.encode("utf-8"))
  if p.returncode != 0:
    raise RuntimeError(f"tee failed for {path}")
  sh(f"sudo chmod {mode} {shlex.quote(path)}")
  
  
def ensure_kv(key, value):
  pattern = re.compile(rf'^\s*{re.escape(key)}\s*=')
  found = False
  for i,l in enumerate(lines):
    if pattern.match(l):
      lines[i] = f"{key} = {value}"
      found = True
      break
  if not found:
    lines.append(f"{key} = {value}")

print('CAM-AI server setup tool')
hw_os_code = sysinfo()
print('Hardware & OS codes:', hw_os_code)
  
if ((((hw_os_code['hw'] == 'raspi' and 4 <= int(hw_os_code['hw_version']) and 4 <= int(hw_os_code['hw_ram']))
    or hw_os_code['hw'] == 'pc')
    and hw_os_code['dist'] == 'debian')
    and int(hw_os_code['dist_version']) in {12, 13}):
  print('Your system is compatible, we continue...')
else:
  print('Your system does not meet our specs, see your hardware & OS codes above.')
  print('We need a PC or a Raspberry Pi with Debian 12 or 13 OS.')
  print('The Raspberry Pi needs to be at least version 4, better version 5.')
  print('Minimum internal RAM 4 GB...')
  exit(1)


if len(sys.argv) >= 3 and sys.argv[1] == '--version':
  special_version = sys.argv[2] 
else:  
  special_version = ''
if special_version:
  zip_url = 'https://github.com/ludgerh/cam-ai/archive/refs/tags/' + special_version + '.zip'
  print('Installing ', special_version)
else:  
  url = 'https://api.github.com/repos/ludgerh/cam-ai/releases/latest'
  response = requests.get(url)
  if response.status_code != 200:
    print('Could not connect to:', url)
    print('Error', response.status_code)
    exit(1)
  response = json.loads(response.text)
  new_version = response['tag_name']
  zip_url = response['zipball_url']
  print('Installing ', new_version)
print() 

if False or run_all:
  selected = False
  while not selected:
    print('Do you want to use the server from localhost? (y/N)')
    uselocal = input(": ")
    uselocal = (uselocal in {'y', 'Y', 'yes', 'Yes', 'YES'})
    if uselocal:
      print('We WILL use localhost.')
    else:
      print('We WILL NOT use localhost')
    print()
    print('What is the internal address to access the server? (leave empty if none)')
    print('(examples: cam-ai-raspi, debian-pc, 192.168.1.42)')
    myip = input(": ")
    if not myip:
      print('We WILL NOT use internal IP,')
    print()
    if uselocal or myip:
      selected = True
    else:  
      print('You need to choose at least one item, try again.')  
      print()

  while not db_pass:
    dbpass1 = (getpass(prompt='Please choose a database password (required): '))
    dbpass2 = (getpass(prompt='Please repeat: '))
    if dbpass1 and dbpass1 == dbpass2:
      db_pass = dbpass1
    else:
      print('The passwords did not match, try again.')  
      print()
  print()

  print('Would you like to grant external access to your Database? (y/N)')
  db_external = input(": ")
  db_external = (db_external in {'y', 'Y', 'yes', 'Yes', 'YES'})
  if db_external:
    print('We WILL grant external DB access.')
  else:
    print('We WILL NOT  grant external DB access.')
  print()
else:
  db_external = True
  db_pass = 'test_pass'
  uselocal = True
  myip = 'cam-ai-raspi'

if False or run_all:
  print('*******************************************')
  print('*                                         *')
  print('*  This will take a couple of minutes.    *')
  print('*  Lean back, have a coffee and watch...  *')
  print('*                                         *')
  print('*******************************************')
  print()
  sleep(10.0)
   
if False or run_all:    
  print('>>>>> Installing MariaDB and database...')   
  subprocess.call(['sudo', 'apt', 'update']) 
  subprocess.call(['sudo', 'apt', '-y', 'upgrade']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'mariadb-server']) 
  subprocess.call(['sudo', 'mariadb-admin', '-u', 'root', 'password', db_pass])
  sql_query("drop user if exists ''@'localhost';")
  sql_query("drop user if exists ''@'%';")
  sql_query("drop user if exists 'root'@'%';")
  sql_query("drop database if exists test;")
  sql_query("drop database if exists `CAM-AI`;")
  sql_query("grant all on *.* to 'CAM-AI'@'localhost' identified by '" + db_pass 
    + "' with grant option;")
  if db_external:
    sql_query("grant all on *.* to 'CAM-AI'@'%' identified by '" + db_pass 
      + "' with grant option;")
  sql_query("flush privileges;")
  sql_query("create database `CAM-AI`;")
  print() 

if False or run_all:
  print('>>>>> Getting and unpacking ZIP...')
  if not os.path.exists('temp'):
    os.makedirs('temp')  
  zip_path = "temp/cam-ai-upgrade.zip"
  response = requests.get(zip_url, stream=True)
  if response.status_code != 200:
    print('Could not connect to:', zip_url)
    print('Error', response.status_code)
    exit(1) 
  with open(zip_path, mode="wb") as file:
    for chunk in response.iter_content(chunk_size=10 * 1024):
      file.write(chunk)    
  with ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall('.')  
  os.remove(zip_path)
  if special_version:
    zipresult = 'cam-ai-' + special_version[1:]
  else:  
    zipresult = glob('ludgerh-cam-ai-*')[0]
  if os.path.exists('backup'):
    rmtree('backup')
  if os.path.exists(installdir):  
    move(installdir, 'backup')  
  move(zipresult, installdir)
  print()

if False or run_all:
  print('>>>>> Installing reqired packages...')
  subprocess.call(['sudo', 'apt', '-y', 'install', 'python3-dev']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'default-libmysqlclient-dev']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'build-essential']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'ffmpeg']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'libgeos-dev']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'redis']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'pkg-config']) 
  print()
 
if False or run_all:  
  print('>>>>> Modifying system config...')
  if int(hw_os_code['dist_version']) <= 12:
    subprocess.call(['sudo', 'sed', '-i', r'/^#\*\*\*\*\* CAM-AI setting/d', 
      '/etc/dhcp/dhclient.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '/^timeout/d', '/etc/dhcp/dhclient.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '$a#***** CAM-AI setting' , 
      '/etc/dhcp/dhclient.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '$atimeout 180;' , '/etc/dhcp/dhclient.conf'])
  if  int(hw_os_code['dist_version']) <= 12:  
    subprocess.call(['sudo', 'sed', '-i', r'/^#\*\*\*\*\* CAM-AI setting/d', 
      '/etc/sysctl.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '/^vm.overcommit_memory/d', '/etc/sysctl.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '/^net.core.somaxconn/d', '/etc/sysctl.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '$a#***** CAM-AI setting' , '/etc/sysctl.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '$avm.overcommit_memory = 1' , 
      '/etc/sysctl.conf']) 
    subprocess.call(['sudo', 'sed', '-i', '$anet.core.somaxconn=1024' , '/etc/sysctl.conf']) 
  else:
    # Beispiel: deine sysctl-Datei
    sysctl_dropin = "/etc/sysctl.d/99-cam-ai.conf"
    content = """#***** CAM-AI setting
    vm.overcommit_memory = 1
    vm.swappiness = 10
    vm.dirty_ratio = 10
    vm.dirty_background_ratio = 5
    net.core.somaxconn = 1024
    vm.transparent_hugepages=never
    """
    write_root_file(sysctl_dropin, content)
    # neu laden
    sh("sudo sysctl --system")
  subprocess.call(['sudo', 'sed', '-i', r'/^#\*\*\*\*\* CAM-AI disabled saving/d', 
    '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^save/d', '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^#save/d', '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#***** CAM-AI disabled saving' , 
    '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#save 900 1' , '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#save 300 10' , '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#save 60 10000' , '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$asave ""' , '/etc/redis/redis.conf']) 
  if db_external:
    subprocess.call(['sudo', 'sed', '-i', r'/^#\*\*\*\*\* CAM-AI setting/d', 
      '/etc/mysql/mariadb.conf.d/50-server.cnf']) 
    subprocess.call(['sudo', 'sed', '-i', '/^bind-address/d', 
      '/etc/mysql/mariadb.conf.d/50-server.cnf']) 
    subprocess.call(['sudo', 'sed', '-i', '$a#***** CAM-AI setting' , 
      '/etc/mysql/mariadb.conf.d/50-server.cnf']) 
    subprocess.call(['sudo', 'sed', '-i', '$abind-address = 0.0.0.0', 
      '/etc/mysql/mariadb.conf.d/50-server.cnf']) 
    subprocess.call(['sudo', 'systemctl', 'restart', 'mariadb']) 
print()

os.chdir(installdir)

if False or run_all:
  print('>>>>> Setting up Python environment...')
  if hw_os_code['hw'] == 'raspi':
    cmd = 'source ~/miniforge3/etc/profile.d/conda.sh; '
  else:  
    cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
  cmd += 'conda activate tf; '
  cmd += 'pip install --upgrade pip; '
  cmd += 'pip install -r requirements.' + hw_os_code['hw'] + '_' + hw_os_code['dist_version'] + '; '
  result = subprocess.call(cmd, shell=True, executable='/bin/bash')

if True or run_all:
  print('>>>>> Modifying ' + installdir + '/passwords.py...')
  if hw_os_code['hw'] == 'raspi':
    cmd = 'source ~/miniforge3/etc/profile.d/conda.sh; '
  else:  
    cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
  cmd += 'conda activate tf; '
  cmd += 'python ' + os.getcwd() + '/get_django_code.py; '
  result = subprocess.check_output(cmd, shell=True, executable='/bin/bash').decode()
  djangocode = result.split('\n')[0]
  if os.path.exists('camai/passwords.py'):
    sourcefile = open('camai/passwords.py', 'r')
  else:  
    sourcefile = open('camai/passwords.py.example', 'r')
  targetfile = open('camai/passwords.py-new', 'w')
  for line in sourcefile:
    if line.startswith('security_key = '):
        line = 'security_key = "' + djangocode + '"\n'
    if line.startswith('localaccess = '):
        line = 'localaccess = ' + str(uselocal) + '\n'
    if line.startswith('myip = '):
        if myip: 
          line = 'myip = ["' + myip + '"]\n'
        else:
          line = 'myip = []\n'
    if line.startswith('db_password = '):
        line = 'db_password = "' + db_pass + '"\n'
    if line.startswith('hw_type = '):
        line = 'hw_type = "' + hw_os_code['hw'] + '"\n'
    if line.startswith('hw_version = '):
        line = 'hw_version = "' + hw_os_code['hw_version'] + '"\n'
    if line.startswith('hw_ram = '):
        line = 'hw_ram = ' + str(hw_os_code['hw_ram']) + '\n'
    if line.startswith('os_type = '):
        line = 'os_type = "' + hw_os_code['dist'] + '"\n'
    if line.startswith('os_version = '):
        line = 'os_version = "' + hw_os_code['dist_version'] + '"\n'
    targetfile.write(line)
  sourcefile.close()
  targetfile.close()
  if os.path.exists('camai/passwords.py'):
    os.remove('/home/cam_ai/cam-ai/camai/passwords.py')
  os.rename('/home/cam_ai/cam-ai/camai/passwords.py-new', 
    '/home/cam_ai/cam-ai/camai/passwords.py')
  print()

if False or run_all:
  print('>>>>> Migrating the database...')
  if hw_os_code['hw'] == 'raspi':
    cmd = 'source ~/miniforge3/etc/profile.d/conda.sh; '
  else:  
    cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
  cmd += 'conda activate tf; '
  cmd += 'python manage.py migrate; '
  result = subprocess.call(cmd, shell=True, executable='/bin/bash')
  copy('runserver.sh', '..')
  os.chdir('..')
  os.chmod('runserver.sh', 0o744)
  
if False or run_all:
  print('>>>>> Modifying the database...')
  subprocess.call(['sudo', 'mariadb-admin', '-u', 'root', 'password', db_pass])
  sql_query("update `CAM-AI`.tf_workers_worker set use_websocket = 0;")
  if hw_os_code['hw'] == 'raspi':
    sql_query("update `CAM-AI`.tf_workers_worker set use_litert = 1;")
  else:  
    sql_query("update `CAM-AI`.tf_workers_worker set use_litert = 0;")
  sql_query("update `CAM-AI`.trainers_trainer set t_type = 2;")
  sql_query("update `CAM-AI`.trainers_trainer set active = 1;")
  if hw_os_code['hw'] == 'raspi':
    sql_query("update `CAM-AI`.trainers_trainer set modeltype = 2;")
    sql_query("update `CAM-AI`.trainers_trainer set wsname = '';")
  else:  
    sql_query("update `CAM-AI`.trainers_trainer set modeltype = 1;")
    sql_query("update `CAM-AI`.trainers_trainer set wsname = 'dummy';")
  
  
  
print()
print('*************************************************')
print('*                                               *')
print('*  Congratulations! Your installation is done.  *')
print('*                                               *')
print('*************************************************')
print()
print('You can now start the server by entering this:')
print('./runserver.sh '+hw_os_code['hw'])
print()
print('And then surf to your new server in the browser using:')
if uselocal:
  print('http://localhost:8000/')
if myip:  
  if uselocal:
    print('or')
  print('http://' + myip + ':8000/')
print()
print('Have a nice day...')


