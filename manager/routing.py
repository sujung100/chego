from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from . import manager_consumers
from . import admin_consumers
from . import test_consumers

websocket_urlpatterns = [
    re_path(r"manager/$", manager_consumers.ManagerConsumer.as_asgi()),
    re_path(r"manager/(?P<room_name>[\w.]+)/$", manager_consumers.ManagerConsumer.as_asgi()),
    # re_path(r"manager/customer_service_center/inquiry/$", admin_consumers.AdminChatConsumer.as_asgi()),
    # re_path(r"manager/customer_service_center/inquiry/(?P<room_name>[\w.]+)/$", admin_consumers.AdminChatConsumer.as_asgi()),
    re_path(r"manager/admin_chat2/(?P<room_name>[\w.]+)/$", admin_consumers.AdminChatConsumer.as_asgi()),
    re_path(r"manager/testchat/(?P<room_name>\w+)/$", test_consumers.ChatConsumer.as_asgi()),
    # re_path(r"reservation/(?P<room_name>\w+)/$", test_consumers.ChatConsumer.as_asgi()),
    
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})