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

urlpatterns = [
  path('cam/<int:camnr>/', views.OneCamView.as_view(), name='onecam'),
  path('cam/<int:camnr>/<int:tokennr>/<str:token>/', views.OneCamView.as_view(), name='onecamtoken'),
  path('detector/<int:detnr>/', views.OneDetView.as_view(), name='onedetector'),
  path('detector/<int:detnr>/<int:tokennr>/<str:token>/', views.OneDetView.as_view(), name='onedetectortoken'),
  path('eventer/<int:evenr>/', views.OneEveView.as_view(), name='oneeventer'),
  path('eventer/<int:evenr>/<int:tokennr>/<str:token>/', views.OneEveView.as_view(), name='oneeventertoken'),
]
