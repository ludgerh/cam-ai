# core/plugin_conf.py
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

from pathlib import Path
from streams.models import stream
from tools.l_tools import load_plugin, compiled_plugin
from .models import plugin as plugin_dbline

def get_subdirs(path):
  if not Path(path).is_dir():
    return([])
  return [p for p in Path(path).iterdir() if p.is_dir()]
  
def update_db(file_path, default):
  # Skip directories without a plugin (e.g. a new, still empty plugin repo)
  if not file_path.exists() and compiled_plugin(file_path) is None:
    return()
  module = load_plugin(file_path)
  plugin_class = getattr(module, 'plugin')
  result = plugin_dbline.objects.update_or_create(
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
  if default and result[0].id != 1 and result[1]:
    if plugin_class.type == 'D':
      stream.objects.filter(det_plugin_id = 1).update(
        det_plugin_id = result[0].id,
      )
    elif plugin_class.type == 'A':
      stream.objects.filter(eve_alarm_plugin_id = 1).update(
        eve_alarm_plugin_id = result[0].id, 
      )
  del module

def plugin_exists(dbline):
  return(Path(dbline.path).parent.is_dir())

def remove_missing():
  # Stream fields referencing plugins of this type, None: no references
  stream_fields = {'D' : 'det_plugin', 'A' : 'eve_alarm_plugin', 'V' : None}
  for dbline in plugin_dbline.objects.filter(type__in = stream_fields.keys()):
    if plugin_exists(dbline):
      continue
    field = stream_fields[dbline.type]
    if field:
      streams = stream.objects.filter(**{field : dbline})
      if streams.exists():
        # Move streams to the default plugin of the same type, otherwise
        # on_delete=SET_DEFAULT would point them to plugin #1 (any type)
        replacement = None
        for candidate in plugin_dbline.objects.filter(
          type = dbline.type,
          default = True,
        ).exclude(id = dbline.id):
          if plugin_exists(candidate):
            replacement = candidate
            break
        if replacement is None:
          continue
        streams.update(**{field : replacement})
    dbline.delete()

for item in get_subdirs(Path.cwd() / 'plugins' / 'detectors'):
  plugin_file = item / 'plugin.py'
  update_db(plugin_file, item.name == 'default')
for item in get_subdirs(Path.cwd() / 'plugins' / 'alarms'):
  plugin_file = item / 'plugin.py'
  update_db(plugin_file, item.name == 'default')
# View plugins have no default
for item in get_subdirs(Path.cwd() / 'plugins' / 'views'):
  plugin_file = item / 'plugin.py'
  update_db(plugin_file, False)
remove_missing()
    
    
    
