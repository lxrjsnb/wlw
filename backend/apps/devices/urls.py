"""
设备模块URL配置
Device app URL configuration
"""
from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # 传感器类型
    path('sensor-types/', views.SensorTypeListView.as_view(), name='sensor_type_list'),
    path('sensor-types/<int:pk>/', views.SensorTypeDetailView.as_view(), name='sensor_type_detail'),

    # 设备管理
    path('', views.DeviceListView.as_view(), name='device_list'),
    path('stats/', views.DeviceStatsView.as_view(), name='device_stats'),
    path('control/<str:device_id>/', views.DeviceControlView.as_view(), name='device_control'),
    path('logs/<str:device_id>/', views.DeviceLogListView.as_view(), name='device_logs'),
    path('<str:device_id>/', views.DeviceDetailView.as_view(), name='device_detail'),
]
