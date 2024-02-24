

import os

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

import manager.routing
import reservation.routing


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chego_pjt.settings')

websocket_urlpatterns = reservation.routing.websocket_urlpatterns + manager.routing.websocket_urlpatterns

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