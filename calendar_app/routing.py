from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from . import user_consumers

websocket_urlpatterns = [
    re_path(r"calendar_app/(?P<room_name>[\w.]+)/$", user_consumers.UserConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})