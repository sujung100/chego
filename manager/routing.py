from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from . import manager_consumers
from . import admin_consumers

websocket_urlpatterns = [
    re_path(r"manager/sung/$", manager_consumers.ManagerConsumer.as_asgi()),
    re_path(r"manager/sung/(?P<room_name>[\w.]+)/$", manager_consumers.ManagerConsumer.as_asgi()),
    re_path(r"manager/sung/admin_chat2/(?P<room_name>[\w.]+)/$", admin_consumers.AdminChatConsumer.as_asgi()),
    
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})