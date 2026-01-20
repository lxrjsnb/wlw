"""
告警模块URL配置
Alarm app URL configuration
"""
from django.urls import path
from . import views

app_name = 'alarms'

urlpatterns = [
    # 告警规则
    path('rules/', views.AlarmRuleListView.as_view(), name='rule_list'),
    path('rules/create/', views.AlarmRuleCreateView.as_view(), name='rule_create'),
    path('rules/<int:pk>/', views.AlarmRuleDetailView.as_view(), name='rule_detail'),

    # 告警记录
    path('records/', views.AlarmRecordListView.as_view(), name='record_list'),
    path('records/<int:pk>/', views.AlarmRecordDetailView.as_view(), name='record_detail'),
    path('records/<int:pk>/resolve/', views.AlarmRecordResolveView.as_view(), name='record_resolve'),

    # 告警统计
    path('stats/', views.AlarmStatsView.as_view(), name='stats'),

    # 告警通知
    path('notifications/', views.AlarmNotificationListView.as_view(), name='notification_list'),
]
