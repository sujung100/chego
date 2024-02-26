"""
ASGI config for chego_pjt project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator


import manager.routing
import calendar_app.routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chego_pjt.settings')

# application = get_asgi_application()


websocket_urlpatterns = calendar_app.routing.websocket_urlpatterns + manager.routing.websocket_urlpatterns
# websocket_urlpatterns = manager.routing.websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
