"""
告警模型
Alarm models for monitoring and alerting
"""
from django.db import models
from django.conf import settings
from apps.devices.models import Device, SensorType


class AlarmRule(models.Model):
    """
    告警规则
    定义触发告警的条件
    """
    RULE_TYPE_CHOICES = [
        ('threshold', '阈值告警'),
        ('rate', '变化率告警'),
        ('offline', '离线告警'),
    ]

    CONDITION_CHOICES = [
        ('greater_than', '大于'),
        ('less_than', '小于'),
        ('equal', '等于'),
        ('not_equal', '不等于'),
        ('between', '区间内'),
        ('outside', '区间外'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '严重'),
    ]

    name = models.CharField(
        verbose_name='规则名称',
        max_length=100
    )
    description = models.CharField(
        verbose_name='描述',
        max_length=500,
        blank=True
    )
    device = models.ForeignKey(
        Device,
        verbose_name='设备',
        on_delete=models.CASCADE,
        related_name='alarm_rules'
    )
    sensor_type = models.ForeignKey(
        SensorType,
        verbose_name='传感器类型',
        on_delete=models.PROTECT,
        related_name='alarm_rules',
        null=True,
        blank=True
    )
    rule_type = models.CharField(
        verbose_name='规则类型',
        max_length=20,
        choices=RULE_TYPE_CHOICES,
        default='threshold'
    )
    condition = models.CharField(
        verbose_name='条件',
        max_length=20,
        choices=CONDITION_CHOICES
    )
    threshold_min = models.FloatField(
        verbose_name='最小阈值',
        null=True,
        blank=True
    )
    threshold_max = models.FloatField(
        verbose_name='最大阈值',
        null=True,
        blank=True
    )
    priority = models.CharField(
        verbose_name='优先级',
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    enabled = models.BooleanField(
        verbose_name='是否启用',
        default=True
    )
    notification_enabled = models.BooleanField(
        verbose_name='是否发送通知',
        default=True
    )
    delay_minutes = models.IntegerField(
        verbose_name='延迟告警(分钟)',
        default=0,
        help_text='持续超阈值多少分钟后触发告警'
    )
    recovery_enabled = models.BooleanField(
        verbose_name='是否告警恢复通知',
        default=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='创建人',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_alarm_rules'
    )
    created_at = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        verbose_name='更新时间',
        auto_now=True
    )

    class Meta:
        db_table = 'alarm_rules'
        verbose_name = '告警规则'
        verbose_name_plural = '告警规则'
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f"{self.name} - {self.device.name}"

    def check_condition(self, value):
        """
        检查是否满足告警条件

        Args:
            value: 当前值

        Returns:
            bool: 是否触发告警
        """
        if self.condition == 'greater_than':
            return self.threshold_max and value > self.threshold_max
        elif self.condition == 'less_than':
            return self.threshold_min and value < self.threshold_min
        elif self.condition == 'equal':
            return (self.threshold_max is not None and
                    abs(value - self.threshold_max) < 0.001)
        elif self.condition == 'between':
            return (self.threshold_min is not None and
                    self.threshold_max is not None and
                    self.threshold_min <= value <= self.threshold_max)
        elif self.condition == 'outside':
            return (self.threshold_min is not None and
                    self.threshold_max is not None and
                    (value < self.threshold_min or value > self.threshold_max))
        return False


class AlarmRecord(models.Model):
    """
    告警记录
    记录触发的告警事件
    """
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('acknowledged', '已确认'),
        ('resolved', '已解决'),
        ('false_positive', '误报'),
    ]

    device = models.ForeignKey(
        Device,
        verbose_name='设备',
        on_delete=models.CASCADE,
        related_name='alarm_records',
        db_index=True
    )
    alarm_rule = models.ForeignKey(
        AlarmRule,
        verbose_name='告警规则',
        on_delete=models.CASCADE,
        related_name='records'
    )
    sensor_type = models.ForeignKey(
        SensorType,
        verbose_name='传感器类型',
        on_delete=models.PROTECT,
        related_name='alarm_records'
    )
    current_value = models.FloatField(
        verbose_name='当前值'
    )
    threshold_value = models.FloatField(
        verbose_name='阈值'
    )
    unit = models.CharField(
        verbose_name='单位',
        max_length=10
    )
    status = models.CharField(
        verbose_name='状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    priority = models.CharField(
        verbose_name='优先级',
        max_length=20,
        choices=AlarmRule.PRIORITY_CHOICES
    )
    message = models.TextField(
        verbose_name='告警消息',
        blank=True
    )
    triggered_at = models.DateTimeField(
        verbose_name='触发时间',
        db_index=True
    )
    acknowledged_at = models.DateTimeField(
        verbose_name='确认时间',
        null=True,
        blank=True
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='确认人',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acknowledged_alarms'
    )
    resolved_at = models.DateTimeField(
        verbose_name='解决时间',
        null=True,
        blank=True
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='解决人',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_alarms'
    )
    resolution_note = models.TextField(
        verbose_name='解决说明',
        blank=True
    )
    notification_sent = models.BooleanField(
        verbose_name='是否已发送通知',
        default=False
    )
    extra_data = models.JSONField(
        verbose_name='额外数据',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )

    class Meta:
        db_table = 'alarm_records'
        verbose_name = '告警记录'
        verbose_name_plural = '告警记录'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['device', 'triggered_at']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['-triggered_at']),
        ]

    def __str__(self):
        return f"{self.device.name} - {self.alarm_rule.name} - {self.triggered_at}"

    @property
    def is_pending(self):
        """是否待处理"""
        return self.status == 'pending'

    @property
    def duration_minutes(self):
        """告警持续时间（分钟）"""
        if self.resolved_at:
            return int((self.resolved_at - self.triggered_at).total_seconds() / 60)
        return None


class AlarmNotification(models.Model):
    """
    告警通知记录
    记录发送的通知
    """
    NOTIFICATION_TYPE_CHOICES = [
        ('websocket', 'WebSocket'),
        ('email', '邮件'),
        ('sms', '短信'),
        ('wechat', '微信'),
    ]

    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sent', '已发送'),
        ('failed', '发送失败'),
    ]

    alarm_record = models.ForeignKey(
        AlarmRecord,
        verbose_name='告警记录',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        verbose_name='通知类型',
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    recipient = models.CharField(
        verbose_name='接收人',
        max_length=200
    )
    status = models.CharField(
        verbose_name='状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(
        verbose_name='错误信息',
        blank=True
    )
    sent_at = models.DateTimeField(
        verbose_name='发送时间',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )

    class Meta:
        db_table = 'alarm_notifications'
        verbose_name = '告警通知'
        verbose_name_plural = '告警通知'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.alarm_record} - {self.notification_type} - {self.recipient}"
