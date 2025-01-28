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

from django.urls import path
from . import views

app_name = 'config'

urlpatterns = [
	path('config/<str:open>/<str:info>/', views.config.as_view(), name='config'),
	path('config/<str:open>/', views.config.as_view(), name='config'),
	path('config/', views.config.as_view(), name='config'),
	path('smtp/<str:info>/', views.smtp.as_view(), name='smtp'),
	path('smtp/', views.smtp.as_view(), name='smtp'),
	path('tags/<str:info>/', views.tags.as_view(), name='tags'),
	path('tags/', views.tags.as_view(), name='tags'),
]

