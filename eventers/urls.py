from django.urls import path

from .views import events, oneevent, eventjpg, eventmp4

urlpatterns = [
	path('events/<int:schoolnr>/', events, name='events'),
	path('oneevent/<int:schoolnr>/<int:eventnr>/', oneevent, name='oneevent'),
	path('eventjpg/<int:eventnr>/', eventjpg, name='eventjpg'),
	path('eventmp4/<int:eventnr>/video.mp4', eventmp4, name='eventmp4'),
]

