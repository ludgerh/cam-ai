from django.urls import path
from sys import argv

if (argv[0].endswith('manage.py') and 'runserver' in argv) or (argv[0].endswith('gunicorn')):
  from .views import getjpg, c_canvas
  urlpatterns = [
	  path('getjpg/<str:mode>/<int:idx>/<int:xdim>/<int:ydim>/<int:counter>/', getjpg, name='getjpg'),
	  path('c_canvas/<str:displaymode>/<str:mode>/<int:idx>/<int:xdim>/<int:ydim>/', c_canvas, name='c_canvas'),
  ]
else:
  urlpatterns = []
  print('Viewers: No further Imports.')
