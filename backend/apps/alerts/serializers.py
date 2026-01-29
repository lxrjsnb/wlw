"""
预警相关序列化器
"""
from rest_framework import serializers
from .models import AlertRule, AlertRecord, AlertNotificationLog
from apps.topics.serializers import TopicSerializer


class AlertRuleSerializer(serializers.ModelSerializer):
    """预警规则序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    rule_type_display = serializers.CharField(source='get_rule_type_display', read_only=True)
    condition_display = serializers.CharField(source='get_condition_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    notify_user_names = serializers.SerializerMethodField()
    is_in_cooldown = serializers.BooleanField(read_only=True)

    class Meta:
        model = AlertRule
        fields = [
            'id', 'topic', 'topic_name', 'rule_type', 'rule_type_display',
            'condition', 'condition_display', 'threshold_value', 'threshold_value_max',
            'priority', 'priority_display', 'enabled', 'is_in_cooldown',
            'notify_websocket', 'notify_email', 'notify_sms', 'notify_users', 'notify_user_names',
            'cooldown_minutes', 'description',
            'created_at', 'updated_at', 'last_triggered_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_triggered_at']

    def get_notify_user_names(self, obj):
        return ', '.join([u.username for u in obj.notify_users.all()])


class AlertRuleCreateSerializer(serializers.ModelSerializer):
    """预警规则创建序列化器"""

    class Meta:
        model = AlertRule
        fields = [
            'topic', 'rule_type', 'condition', 'threshold_value', 'threshold_value_max',
            'priority', 'enabled', 'notify_websocket', 'notify_email', 'notify_sms',
            'notify_users', 'cooldown_minutes', 'description'
        ]


class AlertRecordSerializer(serializers.ModelSerializer):
    """预警记录序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    rule_type = serializers.CharField(read_only=True)
    rule_type_display = serializers.SerializerMethodField()
    priority = serializers.CharField(read_only=True)
    priority_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    triggered_at_formatted = serializers.DateTimeField(source='triggered_at', format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = AlertRecord
        fields = [
            'id', 'topic', 'topic_name', 'alert_rule', 'rule_type', 'rule_type_display',
            'priority', 'priority_display',
            'current_value', 'threshold_value', 'status', 'status_display',
            'message', 'details',
            'acknowledged_by', 'acknowledged_by_name', 'acknowledged_at',
            'resolved_by', 'resolved_by_name', 'resolved_at', 'resolution_note',
            'triggered_at', 'triggered_at_formatted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'triggered_at', 'created_at', 'updated_at']

    def get_rule_type_display(self, obj):
        return obj.alert_rule.get_rule_type_display()

    def get_priority_display(self, obj):
        return obj.alert_rule.get_priority_display()


class AlertRecordListSerializer(serializers.ModelSerializer):
    """预警记录列表序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    rule_type_display = serializers.SerializerMethodField()
    priority_display = serializers.CharField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    triggered_at_formatted = serializers.DateTimeField(source='triggered_at', format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = AlertRecord
        fields = [
            'id', 'topic_name', 'rule_type_display', 'priority_display',
            'status', 'status_display', 'message',
            'current_value', 'threshold_value',
            'triggered_at', 'triggered_at_formatted'
        ]

    def get_rule_type_display(self, obj):
        return obj.alert_rule.get_rule_type_display()


class AlertRecordUpdateSerializer(serializers.ModelSerializer):
    """预警记录更新序列化器"""

    class Meta:
        model = AlertRecord
        fields = ['resolution_note']


class AlertStatsSerializer(serializers.Serializer):
    """预警统计序列化器"""
    total_rules = serializers.IntegerField()
    active_rules = serializers.IntegerField()
    total_records = serializers.IntegerField()
    pending_records = serializers.IntegerField()
    acknowledged_records = serializers.IntegerField()
    resolved_records = serializers.IntegerField()
    today_triggered = serializers.IntegerField()
