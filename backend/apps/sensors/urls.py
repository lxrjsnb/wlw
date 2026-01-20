"""
传感器数据模块URL配置
Sensor data app URL configuration
"""
from django.urls import path
from . import views

app_name = 'sensors'

urlpatterns = [
    # 传感器数据列表
    path('data/', views.SensorDataListView.as_view(), name='data_list'),

    # 创建数据
    path('data/create/', views.SensorDataCreateView.as_view(), name='data_create'),
    path('data/batch/', views.SensorDataBatchCreateView.as_view(), name='data_batch_create'),

    # 获取最新数据
    path('data/latest/<str:device_id>/', views.SensorDataLatestView.as_view(), name='data_latest'),

    # 数据统计
    path('data/statistics/<str:device_id>/', views.SensorDataStatisticsView.as_view(), name='data_statistics'),

    # 历史数据
    path('data/history/<str:device_id>/', views.SensorDataHistoryView.as_view(), name='data_history'),

    # 数据导出
    path('data/export/', views.SensorDataExportView.as_view(), name='data_export'),
]
