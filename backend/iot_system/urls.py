"""
舆情分析系统主路由配置
Main URL configuration for Social Media Sentiment Analysis System
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
        title="Social Media Sentiment Analysis System API",
        default_version='v1',
        description="社交媒体舆情分析系统API文档\n\n"
                   "核心功能：\n"
                   "- 话题管理\n"
                   "- 帖子采集与分析\n"
                   "- 情感分析\n"
                   "- 预警系统\n"
                   "- 趋势分析\n"
                   "- 数据报表",
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
    path('api/v1/topics/', include('apps.topics.urls')),
    path('api/v1/posts/', include('apps.posts.urls')),
    path('api/v1/alerts/', include('apps.alerts.urls')),
    path('api/v1/analysis/', include('apps.analysis.urls')),
]

# 开发环境下提供媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
