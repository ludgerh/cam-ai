from django.urls import path

from .views import index

urlpatterns = [
	path('<str:mode>/', index, name='index'),
	path('', index, name='index'),
]

