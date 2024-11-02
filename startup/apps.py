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

from django.apps import AppConfig
from sys import argv

class StartupConfig(AppConfig):
  default_auto_field = 'django.db.models.BigAutoField'
  name = 'startup'
    
  def ready(self):
    if (argv[0].endswith('manage.py') and 'runserver' not in argv) and (not argv[0].endswith('gunicorn')):
      print('Streams: Not starting extra threads here.')
      return
    from .startup import launch
    launch()
          
