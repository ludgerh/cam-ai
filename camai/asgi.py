"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

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
import eventers.routing
import cleanup.routing

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
        + eventers.routing.websocket_urlpatterns
        + cleanup.routing.websocket_urlpatterns
    )
  ),
})

