#!/usr/bin/env python
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

import os
import sys
import multiprocessing
from setproctitle import setproctitle
from globals.c_globals import initialize as globals_initialize

def main():
  setproctitle("CAM-AI-Manager")
  multiprocessing.set_start_method("spawn", force=True)
  os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'camai.settings')
  globals_initialize()
  if sys.argv[1] == 'runserver':
    from startup.startup import launch
    launch()
  try:
    from django.core.management import execute_from_command_line
  except ImportError as exc:
    raise ImportError(
      "Couldn't import Django. Are you sure it's installed and "
      "available on your PYTHONPATH environment variable? Did you "
      "forget to activate a virtual environment?"
    ) from exc
  execute_from_command_line(sys.argv)

if __name__ == '__main__':
  main()
