# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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
import stat
from django.core.management.utils import get_random_secret_key

print('CAM-AI server setup tool')
print('v 0.9.18')
print()

print('Stopping c_server and nginx processes...')
print()
subprocess.call(['sudo', 'systemctl', 'stop', 'c_server']) 
subprocess.call(['sudo', 'systemctl', 'stop', 'nginx']) 

print('What is your database server password? (required)')
dbpass = input(": ")
print()
print('Do you want to use the server from localhost? (y/N)')
uselocal = input(": ")
uselocal = (uselocal in {'y', 'Y', 'yes', 'Yes', 'YES'})
if uselocal:
  print('We WILL use localhost.')
else:
  print('We WILL NOT use localhost')
print()
print('What is the internal IP to access the server? (leave empty if none)')
print('(example: 192.168.1.42)')
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
print('Do you want to use autostart? (y/N)')
autostart = input(": ")
autostart = (autostart in {'y', 'Y', 'yes', 'Yes', 'YES'})
if autostart:
  print('We WILL activate autostart.')
else:
  print('We WILL NOT activate autostart')
print()

if mydomain:
  print('Modifying and activating Nginx...')
  print('We get the HTTPS-Certificate from Letsencrypt for '+mydomain+'...')
  subprocess.call(['sudo', 'certbot', 'certonly', '--rsa-key-size', '2048', 
    '--standalone', '--agree-tos', '-d', mydomain])
  print()
  subprocess.call(['sudo', 'chown', '-R', 'cam_ai',  '/etc/nginx/sites-available'])
  subprocess.call(['sudo', 'chown', '-R', 'cam_ai',  '/etc/nginx/sites-enabled'])
  sourcefile = open('/etc/nginx/sites-available/cam-ai', 'r')
  targetfile = open('/etc/nginx/sites-available/cam-ai-new', 'w')
  for line in sourcefile:
    if line.startswith('server_name'):
      line = 'server_name ' + mydomain + ';\n'
    if line.startswith('ssl_certificate /'):
      line = 'ssl_certificate /etc/letsencrypt/live/' + mydomain + '/fullchain.pem;\n'
    if line.startswith('ssl_certificate_key /'):
      line = 'ssl_certificate_key /etc/letsencrypt/live/' + mydomain + '/privkey.pem;\n'
    targetfile.write(line)
  sourcefile.close()
  targetfile.close()
  os.remove('/etc/nginx/sites-available/cam-ai')
  os.rename('/etc/nginx/sites-available/cam-ai-new', '/etc/nginx/sites-available/cam-ai')
  subprocess.call(['sudo', 'rm', '/etc/nginx/sites-enabled/cam-ai'])
  subprocess.call(['sudo', 'ln', '-s', '/etc/nginx/sites-available/cam-ai', 
    '/etc/nginx/sites-enabled/'])
  subprocess.call(['sudo', 'chown', '-R', 'root',  '/etc/nginx/sites-available'])
  subprocess.call(['sudo', 'chown', '-R', 'root',  '/etc/nginx/sites-enabled'])
  if myip:
    subprocess.call(['sudo', 'ln', '-s', '/etc/nginx/sites-available/default', 
      '/etc/nginx/sites-enabled/'])
  else:
    subprocess.call(['sudo', 'rm', '/etc/nginx/sites-enabled/cam-ai'])
  subprocess.call(['sudo', 'systemctl', 'enable', 'nginx'])
  print()
  
if autostart:
  subprocess.call(['sudo', 'systemctl', 'enable', 'c_server']) 
  
print('Modifying ~/cam-ai/passwords.py...')
sourcefile = open('/home/cam_ai/cam-ai/camai/passwords.py', 'r')
targetfile = open('/home/cam_ai/cam-ai/camai/passwords.py-new', 'w')
for line in sourcefile:
  if line.startswith('security_key = '):
      line = 'security_key = "' + get_random_secret_key() + '"\n'
  if line.startswith('localaccess = '):
      line = 'localaccess = ' + str(uselocal) + '\n'
  if line.startswith('mydomain = '):
      line = 'mydomain = "' + mydomain + '"\n'
  if line.startswith('myip = '):
      line = 'myip = "' + myip + '"\n'
  if line.startswith('db_password = '):
      line = 'db_password = "' + dbpass + '"\n'
  targetfile.write(line)
sourcefile.close()
targetfile.close()
os.remove('/home/cam_ai/cam-ai/camai/passwords.py')
os.rename('/home/cam_ai/cam-ai/camai/passwords.py-new', 
  '/home/cam_ai/cam-ai/camai/passwords.py')
print()

print('Would you like to reboot the system? (y/N)')
reboot = input(": ")
reboot = (reboot in {'y', 'Y', 'yes', 'Yes', 'YES'})
if reboot:
  os.system('sudo reboot now')

