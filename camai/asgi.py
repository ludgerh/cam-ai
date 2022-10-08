"""
ASGI config for camai project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import viewers.routing
import oneitem.routing
import schools.routing
import ws_predictions.routing
import users.routing
import trainers.routing
import tools.routing
# Insert new apps also below!!!

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'camai.settings')

application = ProtocolTypeRouter({
  'http' : get_asgi_application(),
  'websocket' : AuthMiddlewareStack(
    URLRouter(
      viewers.routing.websocket_urlpatterns
        + oneitem.routing.websocket_urlpatterns
        + schools.routing.websocket_urlpatterns
        + ws_predictions.routing.websocket_urlpatterns
        + users.routing.websocket_urlpatterns
        + trainers.routing.websocket_urlpatterns
        + tools.routing.websocket_urlpatterns
    )
  ),
})

