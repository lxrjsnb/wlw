"""
预警模块URL配置
Alert app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'alerts'

router = DefaultRouter()
router.register(r'rules', views.AlertRuleViewSet, basename='alert_rule')
router.register(r'records', views.AlertRecordViewSet, basename='alert_record')

urlpatterns = [
    path('', include(router.urls)),
]
