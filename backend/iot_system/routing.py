"""
WebSocket路由配置
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/posts/$', consumers.RealtimePostConsumer.as_asgi()),
    re_path(r'ws/alerts/$', consumers.AlertNotificationConsumer.as_asgi()),
]
