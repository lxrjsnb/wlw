"""
预警规则和记录模型
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.topics.models import Topic

User = get_user_model()


class AlertRule(models.Model):
    """预警规则"""

    RULE_TYPE_CHOICES = [
        ('sentiment', '情感告警'),
        ('volume', '数量告警'),
        ('influence', '影响力告警'),
        ('negative_ratio', '负面率告警'),
    ]

    CONDITION_CHOICES = [
        ('greater_than', '大于'),
        ('less_than', '小于'),
        ('equals', '等于'),
        ('not_equals', '不等于'),
        ('between', '区间'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '紧急'),
    ]

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='alert_rules'
    )
    rule_type = models.CharField('规则类型', max_length=20, choices=RULE_TYPE_CHOICES, db_index=True)
    condition = models.CharField('条件', max_length=20, choices=CONDITION_CHOICES)
    threshold_value = models.FloatField('阈值')
    threshold_value_max = models.FloatField('最大阈值', null=True, blank=True, help_text='区间告警时使用')
    priority = models.CharField(
        '优先级',
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    enabled = models.BooleanField('是否启用', default=True, db_index=True)

    # 通知配置
    notify_websocket = models.BooleanField('WebSocket通知', default=True)
    notify_email = models.BooleanField('邮件通知', default=False)
    notify_sms = models.BooleanField('短信通知', default=False)
    notify_users = models.ManyToManyField(
        User,
        verbose_name='通知用户',
        related_name='alert_rules',
        blank=True
    )

    # 额外配置
    cooldown_minutes = models.IntegerField('冷却时间(分钟)', default=30, help_text='同一规则触发间隔')
    description = models.TextField('描述', blank=True)

    # 元数据
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    last_triggered_at = models.DateTimeField('最后触发时间', null=True, blank=True)

    class Meta:
        db_table = 'alerts_alert_rule'
        verbose_name = '预警规则'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['topic', 'enabled']),
            models.Index(fields=['rule_type', 'enabled']),
            models.Index(fields=['priority', 'enabled']),
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.get_rule_type_display()} ({self.get_condition_display()} {self.threshold_value})"

    def is_in_cooldown(self):
        """检查是否在冷却期内"""
        if not self.last_triggered_at:
            return False
        from django.utils import timezone
        cooldown_end = self.last_triggered_at + timezone.timedelta(minutes=self.cooldown_minutes)
        return timezone.now() < cooldown_end

    def get_cache_key(self):
        """获取缓存键"""
        return f"alert_rule_cooldown_{self.id}"


class AlertRecord(models.Model):
    """预警记录"""

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('acknowledged', '已确认'),
        ('resolved', '已解决'),
        ('ignored', '已忽略'),
    ]

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='alert_records',
        db_index=True
    )
    alert_rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        verbose_name='预警规则',
        related_name='records'
    )

    # 触发信息
    current_value = models.FloatField('当前值')
    threshold_value = models.FloatField('阈值')
    status = models.CharField(
        '状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    message = models.TextField('预警消息')
    details = models.JSONField('详细信息', null=True, blank=True)

    # 处理信息
    acknowledged_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='确认人',
        related_name='acknowledged_alerts'
    )
    acknowledged_at = models.DateTimeField('确认时间', null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='解决人',
        related_name='resolved_alerts'
    )
    resolved_at = models.DateTimeField('解决时间', null=True, blank=True)
    resolution_note = models.TextField('处理说明', blank=True)

    # 元数据
    triggered_at = models.DateTimeField('触发时间', db_index=True, auto_now_add=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'alerts_alert_record'
        verbose_name = '预警记录'
        verbose_name_plural = verbose_name
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['topic', '-triggered_at']),
            models.Index(fields=['status', '-triggered_at']),
            models.Index(fields=['alert_rule', '-triggered_at']),
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.message[:50]}"

    def acknowledge(self, user):
        """确认预警"""
        from django.utils import timezone
        self.status = 'acknowledged'
        self.acknowledged_by = user
        self.acknowledged_at = timezone.now()
        self.save()

    def resolve(self, user, note=''):
        """解决预警"""
        from django.utils import timezone
        self.status = 'resolved'
        self.resolved_by = user
        self.resolved_at = timezone.now()
        self.resolution_note = note
        self.save()

    @property
    def priority(self):
        """获取优先级（从规则继承）"""
        return self.alert_rule.priority

    @property
    def rule_type(self):
        """获取规则类型（从规则继承）"""
        return self.alert_rule.rule_type


class AlertNotificationLog(models.Model):
    """预警通知日志"""

    NOTIFICATION_TYPE_CHOICES = [
        ('websocket', 'WebSocket'),
        ('email', '邮件'),
        ('sms', '短信'),
    ]

    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sent', '已发送'),
        ('failed', '发送失败'),
    ]

    alert_record = models.ForeignKey(
        AlertRecord,
        on_delete=models.CASCADE,
        verbose_name='预警记录',
        related_name='notification_logs'
    )
    notification_type = models.CharField(
        '通知类型',
        max_length=20,
        choices=NOTIFICATION_TYPE_CHOICES
    )
    recipient = models.CharField('接收者', max_length=200, help_text='用户ID、邮箱或手机号')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField('错误信息', blank=True)
    sent_at = models.DateTimeField('发送时间', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'alerts_notification_log'
        verbose_name = '预警通知日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_notification_type_display()} -> {self.recipient}"
