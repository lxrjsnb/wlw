from django.contrib import admin
from .models import AlertRule, AlertRecord, AlertNotificationLog


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'rule_type', 'condition', 'threshold_value', 'priority', 'enabled', 'last_triggered_at']
    list_filter = ['rule_type', 'priority', 'enabled']
    search_fields = ['topic__name', 'description']
    filter_horizontal = ['notify_users']


@admin.register(AlertRecord)
class AlertRecordAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'rule_type', 'status', 'current_value', 'threshold_value', 'triggered_at']
    list_filter = ['status', 'alert_rule__rule_type', 'alert_rule__priority']
    search_fields = ['topic__name', 'message']
    readonly_fields = ['triggered_at', 'created_at']
    date_hierarchy = 'triggered_at'

    def rule_type(self, obj):
        return obj.alert_rule.get_rule_type_display()
    rule_type.short_description = '规则类型'


@admin.register(AlertNotificationLog)
class AlertNotificationLogAdmin(admin.ModelAdmin):
    list_display = ['alert_record', 'notification_type', 'recipient', 'status', 'sent_at']
    list_filter = ['notification_type', 'status']
    search_fields = ['recipient', 'error_message']
