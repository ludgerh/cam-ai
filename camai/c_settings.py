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

from camai.passwords import *
from tools.l_sysinfo import sysinfo

si = sysinfo()

system_defaults = {
  'debugpw' : False,
  'debug_daphne' : True,
  'debug_channels' : False,
  'emulatestatic' : False,
  'data_path' : 'data/',
  'db_database' : 'CAM-AI',
  'httpsport' : '',
  'localaccess' : True,
  'myip' : [],
  'mydomain' : '',
  'httpsport' : '',
  'smtp_account' : '',
  'smtp_password' : '',
  'smtp_server' : '',
  'smtp_port' : 587,
  'smtp_email' : '',
  'smtp_use_ssl' : True,
  'hw_type' : si['hw'],
  'hw_version' : si['hw_version'],
  'hw_ram' : si['hw_ram'],
  'os_type' : si['dist'],
  'os_version' : si['dist_version'],
}
result_types = {
  'hw_version' : 'str',
  'os_version' : 'str',
}

def safe_import(item, default=None, logger=None):
  try:
    result = eval(item)
    if item in result_types:
      if result_types[item] == 'str':
        if not isinstance(result, str):
          result = str(result)
          if logger is None:
            print('*** Wrong var type in passwords.py: ' 
              + item + ' should be string. We adjusted for now...')
          else:
            logger.warning('*** Wrong var type in passwords.py: ' + item 
              + ' should be string. We adjusted for now...')
  except NameError:
    if default is None:
      if item in system_defaults:
        result = system_defaults[item]
      else:
        result = None  
    else:    
      result = default
    if logger is None:
      print('*** Missing setting in passwords.py: ' + item + ' - Using default: ' 
        + str(result))
    else:
      logger.warning('*** Missing setting in passwords.py: ' + item 
        + ' - Using default: ' + str(result))
  return(result)
