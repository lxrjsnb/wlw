"""
IoT系统主路由配置
Main URL configuration for IoT System
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Swagger API文档配置
schema_view = get_schema_view(
    openapi.Info(
        title="IoT Environment Monitoring System API",
        default_version='v1',
        description="物联网环境监测系统API文档\n\n"
                   "核心功能：\n"
                   "- 设备管理\n"
                   "- 传感器数据采集\n"
                   "- 实时监控\n"
                   "- 告警管理\n"
                   "- 历史数据查询",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="admin@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),

    # API文档
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),

    # API路由
    path('api/v1/auth/', include('apps.users.urls')),
    path('api/v1/devices/', include('apps.devices.urls')),
    path('api/v1/sensors/', include('apps.sensors.urls')),
    path('api/v1/alarms/', include('apps.alarms.urls')),
]

# 开发环境下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
