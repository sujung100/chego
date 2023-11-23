from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r"manager/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"manager/customer_service_center/inquiry/$", consumers.ChatConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<room_name>\w+)/$", consumers.ChatConsumer.as_asgi()),
]