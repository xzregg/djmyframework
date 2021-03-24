"""
ASGI config for new_django project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/asgi/
"""

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import ws_gateway.routing

application = ProtocolTypeRouter({
        # Explicitly set 'http' key using Django's ASGI application.
        "http"     : django_asgi_app,
        "websocket": AuthMiddlewareStack(
                URLRouter(
                        ws_gateway.routing.websocket_urlpatterns
                )
        ),
})
