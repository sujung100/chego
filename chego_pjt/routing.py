from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path, include

# websocket_urlpatterns = [
#   path("reservation/", include("reservation.routhing")),
# ]

# application = ProtocolTypeRouter({
#     'websocket': AuthMiddlewareStack(
#         URLRouter(
#             websocket_urlpatterns
#         )
#     ),
# })