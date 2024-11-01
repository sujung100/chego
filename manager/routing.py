from django.urls import re_path
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from . import manager_channels
from . import admin_channels
# from . import manager_consumers
# from . import admin_consumers
# from . import test_consumers

websocket_urlpatterns = [
    # 원래
    re_path(r"manager/sung/$", manager_channels.ManagerConsumer.as_asgi()),
    re_path(r"manager/sung/(?P<store_id>\d+)/(?P<room_name>\w+)/$", manager_channels.ManagerConsumer.as_asgi()),
    re_path(r"manager/sung/(?P<room_name>[\w.]+)/$", manager_channels.ManagerConsumer.as_asgi()),
    re_path(r"manager/sung/admin_chat2/(?P<room_name>[\w.]+)/$", admin_channels.AdminChatConsumer.as_asgi()),
    # re_path(r"manager/sung/test/(?P<store_id>\d+)/(?P<room_name>\w+)/$", manager_channels.ManagerConsumer.as_asgi()),
    # 성우님
    re_path(r"manager/sung/test/(?P<store_id>\d+)/(?P<room_name>\w+)/$", manager_channels.CheckConsumer.as_asgi()),
    # 테스트용
    re_path(r"manager/sung/update/(?P<store_id>\d+)/(?P<room_name>\w+)/$", manager_channels.TestConsumer.as_asgi())
    
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})