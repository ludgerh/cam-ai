from django.urls import path
from sys import argv

if (argv[0].endswith('manage.py') and 'runserver' in argv) or (argv[0].endswith('gunicorn')):
  from .views import onecam , onedetector, oneeventer
  urlpatterns = [
	  path('cam/<int:camnr>/', onecam, name='onecam_get'),
	  path('detector/<int:detectornr>/', onedetector, name='onedetector'),
	  path('eventer/<int:eventernr>/', oneeventer, name='oneeventer'),
  ]
else:
  urlpatterns = []
  print('OneItem: No further Imports.')

