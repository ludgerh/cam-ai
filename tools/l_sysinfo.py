"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

import platform

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
  
def osinfo():
  result = {
    'platform' :  platform.platform(),
    'system' : platform.system(),
    'release' : platform.release(),
    'version' : platform.version(),
    'dist' : platform.freedesktop_os_release(),
  }
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
  myos = osinfo()
  result['dist'] = myos['dist']['ID']
  result['dist_version'] = myos['dist']['VERSION_ID']
  return(result) 
  
def is_raspi():
  return(sysinfo()['hw'] == 'raspi')  
  
def is_debian():
  return(sysinfo()['dist'] == 'debian')  
  
def dist_version():
  return(int(sysinfo()['dist_version'])) 
