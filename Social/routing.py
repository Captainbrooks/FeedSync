from django.urls import re_path,path
from .consumers import Messenger,NotificationConsumer


websocket_urlpatterns = [
    re_path(r'ws/messenger/(?P<username>[^/]+)/(?P<other_username>[^/]+)/$', Messenger.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
    
]