# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
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

from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
	path('health/', views.health.as_view(), name='health'),
	path('addschool/', views.addschool.as_view(), name='addschool'),
	path('linkworkers/', views.linkworkers.as_view(), name='linkworkers'),
	path('dbcompression/', views.dbcompression.as_view(), name='dbcompression'),
	path('scan_cams/', views.scan_cams.as_view(), name='scancams'),
	path('inst_cam/<str:ip>/<str:ports>/', views.inst_cam.as_view(), name='instcam'),
	path('shutdown/', views.shutdown.as_view(), name='shutdown'),
	path('upgrade/', views.upgrade.as_view(), name='upgrade'),
	path('backup/', views.backup.as_view(), name='backup'),
	path('restore/', views.restore.as_view(), name='restore'),
	path('downbackup/backup.zip', views.downbackup, name='downbackup'),
]

