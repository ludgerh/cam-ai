from django.apps import AppConfig
from sys import argv


class StreamsConfig(AppConfig):
  default_auto_field = 'django.db.models.BigAutoField'
  name = 'streams'

  def ready(self):
    if (argv[0].endswith('manage.py') and 'runserver' not in argv) and (not argv[0].endswith('gunicorn')):
      print('Streams: Not starting extra threads here.')
      return
    from .startup import run
    run()
      
