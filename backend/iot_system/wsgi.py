"""
WSGI配置 - 用于生产环境部署
WSGI config for IoT project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_system.settings')

application = get_wsgi_application()
