from pratic_django.urls import re_path
from .consumers import MyConsumer
from channels.routing import ProtocolTyperouter, URLRouter
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/some_path/', consumers.MyConsumer.as_asgi()),
]
