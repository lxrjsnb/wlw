"""
告警模块序列化器
Alarm serializers for alarm management
"""
from rest_framework import serializers
from .models import AlarmRule, AlarmRecord, AlarmNotification
from apps.devices.serializers import DeviceSerializer, SensorTypeSerializer


class AlarmRuleSerializer(serializers.ModelSerializer):
    """
    告警规则序列化器
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    sensor_type_name = serializers.CharField(source='sensor_type.name', read_only=True)
    sensor_type_unit = serializers.CharField(source='sensor_type.unit', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = AlarmRule
        fields = [
            'id', 'name', 'description', 'device', 'device_name',
            'sensor_type', 'sensor_type_name', 'sensor_type_unit',
            'rule_type', 'condition', 'threshold_min', 'threshold_max',
            'priority', 'enabled', 'notification_enabled', 'delay_minutes',
            'recovery_enabled', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class AlarmRuleCreateSerializer(serializers.ModelSerializer):
    """
    告警规则创建序列化器
    """
    class Meta:
        model = AlarmRule
        fields = [
            'name', 'description', 'device', 'sensor_type',
            'rule_type', 'condition', 'threshold_min', 'threshold_max',
            'priority', 'enabled', 'notification_enabled', 'delay_minutes',
            'recovery_enabled'
        ]

    def validate(self, attrs):
        """验证告警规则"""
        condition = attrs.get('condition')
        threshold_min = attrs.get('threshold_min')
        threshold_max = attrs.get('threshold_max')

        # 根据条件验证阈值
        if condition in ['greater_than', 'less_than']:
            if threshold_max is None:
                raise serializers.ValidationError({'threshold_max': '请设置阈值'})

        elif condition in ['between', 'outside']:
            if threshold_min is None or threshold_max is None:
                raise serializers.ValidationError('请设置最小和最大阈值')
            if threshold_min >= threshold_max:
                raise serializers.ValidationError('最小阈值必须小于最大阈值')

        return attrs

    def create(self, validated_data):
        """创建告警规则"""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def to_representation(self, instance):
        """返回完整的规则信息"""
        return AlarmRuleSerializer(instance).data


class AlarmRecordSerializer(serializers.ModelSerializer):
    """
    告警记录序列化器
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_id_str = serializers.CharField(source='device.device_id', read_only=True)
    alarm_rule_name = serializers.CharField(source='alarm_rule.name', read_only=True)
    sensor_type_name = serializers.CharField(source='sensor_type.name', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    acknowledged_by_name = serializers.CharField(source='acknowledged_by.username', read_only=True)
    resolved_by_name = serializers.CharField(source='resolved_by.username', read_only=True)
    duration_minutes = serializers.ReadOnlyField()

    class Meta:
        model = AlarmRecord
        fields = [
            'id', 'device', 'device_name', 'device_id_str',
            'alarm_rule', 'alarm_rule_name',
            'sensor_type', 'sensor_type_name',
            'current_value', 'threshold_value', 'unit',
            'status', 'status_display', 'priority', 'priority_display',
            'message', 'triggered_at', 'acknowledged_at', 'acknowledged_by',
            'acknowledged_by_name', 'resolved_at', 'resolved_by',
            'resolved_by_name', 'resolution_note', 'notification_sent',
            'extra_data', 'created_at', 'duration_minutes'
        ]
        read_only_fields = ['id', 'triggered_at', 'created_at']


class AlarmRecordUpdateSerializer(serializers.ModelSerializer):
    """
    告警记录更新序列化器（处理告警）
    """
    class Meta:
        model = AlarmRecord
        fields = ['status', 'resolution_note']

    def validate_status(self, value):
        """验证状态"""
        valid_transitions = {
            'pending': ['acknowledged', 'resolved', 'false_positive'],
            'acknowledged': ['resolved', 'false_positive'],
            'resolved': [],
            'false_positive': []
        }

        instance = self.instance
        if value not in valid_transitions.get(instance.status, []):
            raise serializers.ValidationError(
                f'不能从 {instance.status} 转换到 {value}'
            )
        return value

    def update(self, instance, validated_data):
        """更新告警记录"""
        status = validated_data.get('status')
        user = self.context['request'].user

        if status == 'acknowledged':
            instance.acknowledged_by = user
            instance.acknowledged_at = timezone.now()

        if status in ['resolved', 'false_positive']:
            instance.resolved_by = user
            instance.resolved_at = timezone.now()

        instance.status = status
        instance.resolution_note = validated_data.get('resolution_note')
        instance.save()

        return instance


class AlarmNotificationSerializer(serializers.ModelSerializer):
    """
    告警通知序列化器
    """
    alarm_device_name = serializers.CharField(source='alarm_record.device.name', read_only=True)
    notification_type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AlarmNotification
        fields = [
            'id', 'alarm_record', 'alarm_device_name',
            'notification_type', 'notification_type_display',
            'recipient', 'status', 'status_display',
            'error_message', 'sent_at', 'created_at'
        ]
        read_only_fields = ['id', 'sent_at', 'created_at']


from django.utils import timezone
