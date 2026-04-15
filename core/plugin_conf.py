"""
Copyright (C) 2026 by the CAM-AI team, info@cam-ai.de
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

import sys
import importlib.util
from pathlib import Path
from .models import plugin as plugin_dbline

def get_subdirs(path):
  return [p for p in Path(path).iterdir() if p.is_dir()]
  
def update_db(file_path, default):
  module_name = f'plugin_{file_path.parent.name}'
  spec = importlib.util.spec_from_file_location(module_name, file_path)
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)
  plugin_class = getattr(module, 'plugin')
  plugin_dbline.objects.update_or_create(
    defaults = {
      'type' : plugin_class.type,
      'default' : default,
      'name' : plugin_class.name,
      'version' : plugin_class.version,
      'maker' : plugin_class.maker,
      'description' : plugin_class.description,
      'copyright' : plugin_class.copyright,
    }, 
    path = file_path,
  )
  del module

for item in get_subdirs(Path.cwd() / 'plugins' / 'detectors'):
  plugin_file = item / 'plugin.py'
  update_db(plugin_file, item.name == 'default')
    
    
    
