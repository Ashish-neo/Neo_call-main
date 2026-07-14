"""
ASGI config for pratic_django project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""
import os

from channels.routing import ProtocolTypeRouter , URLRouter
from home.routing import websocket_urlpatterns
from pratic_django import *
from home import routing
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from pratic_django.home.routing import application as websocket_routes

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pratic_django.settings')

# application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            pratic_django.home.routing.websocket_urlpatterns
        )
    ),
})