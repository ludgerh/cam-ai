# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
# More information and komplete source: https://github.com/ludgerh/cam-ai
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

import subprocess
import os
import requests
import json
from time import sleep
from shutil import move, rmtree, copy
from zipfile import ZipFile
from glob import glob
from getpass import getpass
import platform

installdir = 'cam-ai'
root_db_pass = None
cam_ai_db_pass = None

def sql_query(command):
  subprocess.call(['mariadb', '-u', 'root', '-p'+root_db_pass, '-e', command]) 

print('CAM-AI server setup tool')

print('Just for in case: Stopping c_server process (red failure message should be OK)...')
subprocess.call(['sudo', 'systemctl', 'stop', 'c_server']) 
print()

os_code = platform.release()
if os_code == '6.1.0-13-amd64':
  os_code = 'debian12'
  env_type = 'conda'
elif (os_code == '6.1.0-rpi4-rpi-v8'
  or os_code == '6.1.0-rpi6-rpi-v8'):
  os_code = 'raspi12'
  env_type = 'venv'
else:
  print('Unknown OS code:', os_code) 
  exit(1)
print('Detected OS:', os_code)
print('Environment Type:', env_type)
print()

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
  print('What is the external domain to access the server? (leave empty if none)')
  print('(example: mydomain.org)')
  mydomain = input(": ")
  if not mydomain:
    print('We WILL NOT use external domain,')
  print()
  if uselocal or myip or mydomain:
    selected = True
  else:  
    print('You need to choose at least one item, try again.')  
    print()

while not root_db_pass:
  dbpass1 = (getpass(prompt='Please choose a database root password (required): '))
  dbpass2 = (getpass(prompt='Please repeat: '))
  if dbpass1 and dbpass1 == dbpass2:
    root_db_pass = dbpass1
  else:
    print('The passwords did not match, try again.')  
    print()
print()

while not cam_ai_db_pass:
  dbpass1 = (getpass(prompt='Please choose a database password for the user CAM-AI (required): '))
  dbpass2 = (getpass(prompt='Please repeat: '))
  if dbpass1 and dbpass1 == dbpass2:
    cam_ai_db_pass = dbpass1
  else:
    print('The passwords did not match, try again.')  
    print()
print()

print('*******************************************')
print('*                                         *')
print('*  This will take a couple of minutes.    *')
print('*  Lean back, have a coffee and watch...  *')
print('*                                         *')
print('*******************************************')
print()
sleep(10.0)
    
print('>>>>> Installing MariaDB and database...')   
subprocess.call(['sudo', 'apt', 'update']) 
subprocess.call(['sudo', 'apt', '-y', 'upgrade']) 
subprocess.call(['sudo', 'apt', '-y', 'install', 'mariadb-server']) 
subprocess.call(['sudo', 'mariadb-admin', '-u', 'root', 'password', root_db_pass])
sql_query("drop user if exists ''@'localhost';")
sql_query("drop user if exists ''@'%';")
sql_query("drop user if exists 'root'@'%';")
sql_query("drop database if exists test;")
sql_query("drop database if exists `CAM-AI`;")
sql_query("grant all on *.* to 'CAM-AI'@'localhost' identified by '" + cam_ai_db_pass + "' with grant option;")
sql_query("create database `CAM-AI`")
print() 

if True:
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
  zipresult = glob('ludgerh-cam-ai-*')[0]

  if os.path.exists('backup'):
    rmtree('backup')
  if os.path.exists(installdir):  
    move(installdir, 'backup')  
  move(zipresult, installdir)
  print()

if True:
  print('>>>>> Installing reqired packages...')
  subprocess.call(['sudo', 'apt', '-y', 'install', 'python3-dev']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'default-libmysqlclient-dev']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'build-essential']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'ffmpeg']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'libgeos-dev']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'redis']) 
  subprocess.call(['sudo', 'apt', '-y', 'install', 'pkg-config']) 
  if env_type == 'venv':
    subprocess.call(['sudo', 'apt', '-y', 'install', 'python3-venv']) 
  else:
    pass #Conda  
  print()
    
  print('>>>>> Modifying system config...')
  subprocess.call(['sudo', 'sed', '-i', '/^#\*\*\*\*\* CAM-AI setting/d', '/etc/dhcp/dhclient.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^timeout/d', '/etc/dhcp/dhclient.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#***** CAM-AI setting' , '/etc/dhcp/dhclient.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$atimeout 180;' , '/etc/dhcp/dhclient.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^#\*\*\*\*\* CAM-AI setting/d', '/etc/sysctl.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^vm.overcommit_memory/d', '/etc/sysctl.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^net.core.somaxconn/d', '/etc/sysctl.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#***** CAM-AI setting' , '/etc/sysctl.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$avm.overcommit_memory = 1' , '/etc/sysctl.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$anet.core.somaxconn=1024' , '/etc/sysctl.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^#\*\*\*\*\* CAM-AI disabled saving/d', '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^save/d', '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '/^#save/d', '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#***** CAM-AI disabled saving' , '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#save 900 1' , '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#save 300 10' , '/etc/redis/redis.conf']) 
  subprocess.call(['sudo', 'sed', '-i', '$a#save 60 10000' , '/etc/redis/redis.conf']) 
  
  #subprocess.call(['sudo', 'touch', '/etc/sudoers.d/010_CAM-AI_reboot_privilege']) 
  #subprocess.call(['sudo', 'sed', '-i', '$acam_ai ALL=(root) NOPASSWD: /sbin/reboot' , '/etc/sudoers.d/010_CAM-AI_reboot_privilege']) 
  #cmd = 'echo "cam_ai ALL=(root) NOPASSWD: /sbin/reboot" | sudo tee -a /etc/sudoers.d/010_CAM-AI_reboot_privilege'
  #subprocess.call(cmd) 
  
  print()

os.chdir(installdir)

print('>>>>> Setting up Python environment...')
if env_type == 'venv':
  if not os.path.exists('env'):
    subprocess.call(['python', '-m', 'venv', 'env']) 
  cmd = 'source env/bin/activate; '
else: #conda
  cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
  cmd += 'conda activate tf; '
cmd += 'pip install --upgrade pip; '
cmd += 'pip install -r requirements.' + os_code + '; '
result = subprocess.check_output(cmd, shell=True, executable='/bin/bash').decode()
for line in result.split('\n'):
  print(line); 
  
print('>>>>> Modifying ' + installdir + '/passwords.py...')
if env_type == 'venv':
  cmd = 'source env/bin/activate; '
else: #conda
  cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
  cmd += 'conda activate tf; '
cmd += 'python get_django_code.py; '
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
  if line.startswith('mydomain = '):
      line = 'mydomain = "' + mydomain + '"\n'
  if line.startswith('myip = '):
      line = 'myip = "' + myip + '"\n'
  if line.startswith('db_password = '):
      line = 'db_password = "' + cam_ai_db_pass + '"\n'
  if line.startswith('os_type = '):
      line = 'os_type = "' + os_code + '"\n'
  if line.startswith('env_type = '):
      line = 'env_type = "' + env_type + '"\n'
  targetfile.write(line)
sourcefile.close()
targetfile.close()
if os.path.exists('camai/passwords.py'):
  os.remove('/home/cam_ai/cam-ai/camai/passwords.py')
os.rename('/home/cam_ai/cam-ai/camai/passwords.py-new', 
  '/home/cam_ai/cam-ai/camai/passwords.py')
print()

print('>>>>> Migrating the database...')
if env_type == 'venv':
  cmd = 'source env/bin/activate; '
else: #conda
  cmd = 'source ~/miniconda3/etc/profile.d/conda.sh; '
  cmd += 'conda activate tf; '
cmd += 'python manage.py migrate; '
result = subprocess.check_output(cmd, shell=True, executable='/bin/bash').decode()
for line in result.split('\n'):
  print(line); 
runserverfile = 'runserver.sh'
#copy(runserverfile, '..')
os.chdir('..')
os.chmod(runserverfile, 0o744)
print()
print('*************************************************')
print('*                                               *')
print('*  Congratulations! Your installation is done.  *')
print('*                                               *')
print('*************************************************')
print()
print('You can now start the server by entering this:')
print('./runserver.sh')
print()
print('And then surf to your new server in the browser using:')
print('http://cam-ai-raspi:8000/')
print()
print('Have a nice day...')


