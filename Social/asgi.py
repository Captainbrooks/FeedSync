import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Social.settings')
from django.core.asgi import get_asgi_application
application=get_asgi_application()


from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path


from .routing import websocket_urlpatterns  

application = ProtocolTypeRouter({
    "http": application,
    
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
