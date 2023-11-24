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

from .views import events, oneevent, eventjpg, eventmp4, eventwebm, alarm

urlpatterns = [
	path('events/<int:schoolnr>/', events, name='events'),
	path('oneevent/<int:schoolnr>/<int:eventnr>/', oneevent, name='oneevent'),
	path('eventjpg/<int:eventnr>/video.jpg', eventjpg, name='eventjpg'),
	path('eventjpg/<int:eventnr>/<int:tokennr>/<str:token>/video.jpg', eventjpg, name='eventjpgtoken'),
	path('eventmp4/<int:archivenr>/video.mp4', eventmp4, name='eventmp4'),
	path('eventmp4/<int:archivenr>/<int:eventnr>/video.mp4', eventmp4, name='eventmp4event'),
	path('eventmp4/<int:eventnr>/<int:tokennr>/<str:token>/video.mp4', eventmp4, name='eventmp4token'),
	path('eventwebm/<int:archivenr>/video.webm', eventwebm, name='eventwebm'),
	path('eventwebm/<int:archivenr>/<int:eventnr>/video.webm', eventwebm, name='eventwebmevent'),
	path('eventwebm/<int:eventnr>/<int:tokennr>/<str:token>/video.webm', eventwebm, name='eventwebmtoken'),
	path('alarm/<int:schoolnr>/', alarm, name='alarm'),
]

