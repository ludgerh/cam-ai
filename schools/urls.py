from django.urls import path

from .views import images, classroom, getbmp, getbigbmp

urlpatterns = [
	path('images/<int:schoolnr>/', images, name='images'),
	path('classroom/<int:schoolnr>/', classroom, name='classroom'),
	path('getbmp/<int:schoolnr>/<str:name>/', getbmp, name='getbmp'),
	path('getbigbmp/<int:schoolnr>/<str:name>/', getbigbmp, name='getbigbmp'),
]

