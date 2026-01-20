"""
ASGI配置 - 用于WebSocket连接
ASGI config for WebSocket support
"""
import os
import django
from django.core.asgi import get_asgi_application

# 初始化Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_system.settings')
django.setup()

# 导入路由配置
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import iot_system.routing

application = ProtocolTypeRouter({
    # HTTP协议处理 - 使用Django的ASGI应用
    "http": get_asgi_application(),

    # WebSocket协议处理
    "websocket": AuthMiddlewareStack(
        URLRouter(
            iot_system.routing.websocket_urlpatterns
        )
    ),
})
