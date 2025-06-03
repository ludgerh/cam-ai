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

from django.contrib import admin
from django.urls import path, include
from sys import argv

if (argv[0].endswith('manage.py') and 'runserver' in argv) or (argv[0].endswith('gunicorn')):
  urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('nic/', include('dyndns.urls')),
    path('index/', include('index.urls')),
    path('oneitem/', include('oneitem.urls')),
    path('schools/', include('schools.urls')),
    path('trainers/', include('trainers.urls')),
    path('eventers/', include('eventers.urls')),
    path('users/', include('users.urls')),
    path('tools/', include('tools.urls')),
    path('cleanup/', include('cleanup.urls')),
    path('config/', include('config.urls')),
    path('', include('index.urls')),
  ]
else:
  urlpatterns = []
  print('camai/urls.py: No further Imports.')

