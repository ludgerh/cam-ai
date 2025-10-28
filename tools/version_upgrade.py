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

from collections import OrderedDict
from .l_tools import version_flat, version_full
from camai.c_settings import safe_import

proc_dict = OrderedDict()

def temp_func():
  from tf_workers.models import worker
  worker.objects.all().update(timeout = 1.0)
proc_dict[version_flat('1.4.7i')] = temp_func

def temp_func():
  hw_type = safe_import('hw_type') 
  if hw_type == 'raspi': 
    from tf_workers.models import worker
    from trainers.models import trainer
    worker.objects.all().update(use_litert = True)
    trainer.objects.all().update(modeltype = 2)  
proc_dict[version_flat('1.4.7o')] = temp_func

def temp_func():
  hw_type = safe_import('hw_type') 
  if hw_type == 'raspi': 
    from tf_workers.models import worker
    worker.objects.all().update(use_websocket = False)
proc_dict[version_flat('1.5.1')] = temp_func

def temp_func():
  from tf_workers.models import worker
  worker.objects.all().update(timeout = 0.1)
proc_dict[version_flat('1.6.6a')] = temp_func

def temp_func():
  from .l_sysinfo import is_raspi
  from streams.models import stream 
  stream.objects.all().update(
    cam_fpslimit = 0,
    det_fpslimit = 2.0,
    eve_fpslimit = 0,
  )
proc_dict[version_flat('1.6.6d')] = temp_func

def temp_func():
  from pathlib import Path
  #Path('/home/cam_ai').chmod(0o711) 
  Path('..').chmod(0o711) 
proc_dict[version_flat('1.9.6a')] = temp_func

def temp_func():
  from tf_workers.models import school
  school.objects.all().update(
    l_rate_start = 0,
    l_rate_stop = 0,
  )
proc_dict[version_flat('1.6.6g')] = temp_func

def version_upgrade(old_str, new_str):
  oldflat = version_flat(old_str)
  newflat = version_flat(new_str)
  lastflat = oldflat
  if newflat <= oldflat:
    return()
  print('########## VersionUpgrade:', old_str, '--->',new_str)
  for item in proc_dict:
    if item > oldflat and item <= newflat:
      print(version_full(lastflat), '>', version_full(item))
      proc_dict[item]()
      lastflat = item
