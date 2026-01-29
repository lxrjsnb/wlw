"""
话题模块URL配置
Topic app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'topics'

router = DefaultRouter()
router.register(r'platforms', views.PlatformViewSet, basename='platform')
router.register(r'', views.TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
]
