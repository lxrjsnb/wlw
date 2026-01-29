"""
分析模块URL配置
Analysis app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'analysis'

router = DefaultRouter()
router.register(r'logs', views.AnalysisLogViewSet, basename='analysis_log')
router.register(r'', views.AnalysisViewSet, basename='analysis')

urlpatterns = [
    path('', include(router.urls)),
]
