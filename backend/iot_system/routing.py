"""
WebSocket路由配置
WebSocket routing configuration
"""
from django.urls import re_path
from . import consumers

# WebSocket URL模式
websocket_urlpatterns = [
    # 实时数据推送
    re_path(r'^ws/realtime/$', consumers.RealtimeDataConsumer.as_asgi()),
    re_path(r'^ws/realtime/(?P<device_id>\w+)/$', consumers.RealtimeDataConsumer.as_asgi()),

    # 告警推送
    re_path(r'^ws/alarms/$', consumers.AlarmConsumer.as_asgi()),
]
