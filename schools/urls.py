"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty o
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""

from django.urls import path
from . import views

urlpatterns = [
	path('images/<int:schoolnr>/', views.images, name='images'),
	path('classroom/<int:streamnr>/', views.classroom, name='classroom'),
	path('upload/<int:schoolnr>/', views.upload_file, name='upload_file'),
	path('getbmp/<int:mode>/<int:framenr>/<int:outtype>/<int:xycontained>'
    + '/<int:x>/<int:y>/', views.getbmp, name='getbmp'),
	path('getbmp/<int:mode>/<int:framenr>/<int:outtype>/<int:xycontained>'
    + '/<int:x>/<int:y>/<int:tokennr>/<str:token>/', views.getbmp, name='getbmptoken'),
	path('getbigbmp/<int:mode>/<int:framenr>/', views.getbigbmp, name='getbigbmp'),
	path('getbigbmp/<int:mode>/<int:framenr>/<int:tokennr>/<str:token>/', 
    views.getbigbmp, name='getbigbmptoken'),
	path('getbigmp4/<int:archivenr>/video.html', views.getbigmp4, name='getbigmp4'),
	path('getbigmp4/<int:eventnr>/<int:tokennr>/<str:token>/video.html', 
    views.getbigmp4, name='getbigmp4token'),
]

