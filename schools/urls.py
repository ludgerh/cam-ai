# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
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

from .views import images, classroom, getbmp, getbigbmp, getbigmp4

urlpatterns = [
	path('images/<int:schoolnr>/', images, name='images'),
	path('classroom/<int:schoolnr>/', classroom, name='classroom'),
	path('getbmp/<int:mode>/<int:framenr>/<int:outtype>/<int:xycontained>/<int:x>/<int:y>/', getbmp, name='getbmp'),
	path('getbmp/<int:mode>/<int:framenr>/<int:outtype>/<int:xycontained>/<int:x>/<int:y>/<int:tokennr>/<str:token>/', getbmp, name='getbmptoken'),
	path('getbigbmp/<int:mode>/<int:framenr>/', getbigbmp, name='getbigbmp'),
	path('getbigbmp/<int:mode>/<int:framenr>/<int:tokennr>/<str:token>/', getbigbmp, name='getbigbmptoken'),
	path('getbigmp4/<int:eventnr>/video.html', getbigmp4, name='getbigmp4'),
	path('getbigmp4/<int:eventnr>/<int:tokennr>/<str:token>/video.html', getbigmp4, name='getbigmp4token'),
]

