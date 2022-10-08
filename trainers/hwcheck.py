# Copyright (C) 2021 Ludger Hellerhoff, ludger@booker-hellerhoff.de
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
from time import sleep

def readoutput(command, params=None):
	if params is None:
		callline = [command]
	else:
		callline = [command, params]
	try:
		return(subprocess.run([command], stdout=subprocess.PIPE).stdout.decode('utf-8'))
	except FileNotFoundError:
		return(None)

def average(what):
	result = 0.0
	count = 0
	for i in range(10):
		temp = what()
		if temp is not None:
			result += temp
			count += 1
			sleep(djconf.getconfigfloat('long_brake', 1.0))
	if count == 0:
		return(None)
	else:
		return(result / count)

def getlinewith(key, command, count=0, params=None):
  lines = readoutput(command, params=None)
  if lines is None:
    return(None)
  else:
    lines = lines.splitlines()
  for line in lines:
    if key in line:
      if count == 0:
        return(line)
      else:
        count -= 1
  return(None)

def getcputemp():
	line = getlinewith('Package id 0:', 'sensors')
	if line is None:
		line = getlinewith('CPUTIN:', 'sensors')
		if line is None:
			return(0)
	line = line.split('+',1)[1]
	line = line.split('°',1)[0]
	return(float(line))

def getcpufan1():
	line = getlinewith('fan1:', 'sensors')
	if line is None:
		return(0)
	else:
		line = line.split(':',1)[1]
		line = line.split('RPM',1)[0]
		return(float(line))

def getcpufan2():
	line = getlinewith('fan2:', 'sensors')
	if line is None:
		return(0)
	else:
		line = line.split(':',1)[1]
		line = line.split('RPM',1)[0]
		return(float(line))

def getgputemp(count = 0):
	line = getlinewith('Default', 'nvidia-smi', count)
	if line is None:
		return(0)
	else:
		line = line.split('%',1)[1]
		line = line.split('C',1)[0]
		return(float(line))

def getgpufan(count = 0):
	line = getlinewith('Default', 'nvidia-smi', count)
	if line is None:
		return(0)
	else:
		line = line.split('|',1)[1]
		line = line.split('%',1)[0]
		return(float(line))

def getcputemp_av():
	return (average(getcputemp))

def getgputemp_av():
	return (average(getgputemp))

def getcpufan1_av():
	return (average(getcpufan1))

def getcpufan2_av():
	return (average(getcpufan2))

def getgpufan_av():
	return (average(getgpufan))
