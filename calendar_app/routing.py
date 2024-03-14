from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from . import user_consumers
from . import main_consumers

websocket_urlpatterns = [
    # re_path(r"calendar_app/(?P<room_name>[\w.]+)/$", user_consumers.UserConsumer.as_asgi()),
    re_path(r"calendar_app/$", main_consumers.CheckingRsvConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})