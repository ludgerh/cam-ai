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

from django.urls import path
from . import views

app_name = 'tools'

urlpatterns = [
	path('addschool/', views.addschool.as_view(), name='addschool'),
	path('linkservers/', views.linkservers.as_view(), name='linkservers'),
	path('inst_cam_easy/', views.inst_cam_easy.as_view(), name='inst_cam_easy'),
	path(
	  'inst_cam_expert/<str:ip>/<str:ports>/', 
	  views.inst_cam_expert.as_view(), 
	  name='inst_cam_expert',
	),
	path('scan_cam_expert/', views.scan_cam_expert.as_view(), name='scan_cam_expert'),
	path('inst_virt_cam/', views.inst_virt_cam.as_view(), name='inst_virt_cam'),
	path(
	  'virt_cam_error/<str:text>/<int:length>/', 
	  views.virt_cam_error.as_view(), 
	  name='virt_cam_error',
	),
	path('shutdown/', views.shutdown.as_view(), name='shutdown'),
	path('sendlogs/', views.sendlogs.as_view(), name='sendlogs'),
	path('upgrade/', views.upgrade.as_view(), name='upgrade'),
	path('backup/', views.backup.as_view(), name='backup'),
	path('restore/', views.restore.as_view(), name='restore'),
	path('downbackup/backup.zip', views.downbackup, name='downbackup'),
	path('downbackup/backup.zip/<int:school_nr>/', views.downbackup, name='downbackup'),
	path('process_restore', views.process_restore.as_view(), name='process_restore'),
	path('logout/', views.logout_and_redirect, name='logout_and_redirect'),
]

