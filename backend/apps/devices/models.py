"""
设备模型
Device models for IoT system
"""
from django.db import models
from django.conf import settings


class SensorType(models.Model):
    """
    传感器类型
    定义支持的传感器类型及其配置
    """
    SENSOR_CATEGORY_CHOICES = [
        ('environment', '环境监测'),
        ('air_quality', '空气质量'),
        ('other', '其他'),
    ]

    name = models.CharField(
        verbose_name='传感器名称',
        max_length=50
    )
    code = models.CharField(
        verbose_name='传感器代码',
        max_length=20,
        unique=True,
        db_index=True
    )
    unit = models.CharField(
        verbose_name='单位',
        max_length=10,
        help_text='如: °C, %, μg/m³'
    )
    category = models.CharField(
        verbose_name='分类',
        max_length=20,
        choices=SENSOR_CATEGORY_CHOICES,
        default='environment'
    )
    description = models.CharField(
        verbose_name='描述',
        max_length=200,
        blank=True
    )
    icon = models.CharField(
        verbose_name='图标',
        max_length=50,
        blank=True,
        help_text='前端使用的图标名称'
    )
    color = models.CharField(
        verbose_name='颜色',
        max_length=20,
        default='#409EFF',
        help_text='图表显示颜色'
    )
    min_value = models.FloatField(
        verbose_name='最小值',
        null=True,
        blank=True,
        help_text='正常范围最小值'
    )
    max_value = models.FloatField(
        verbose_name='最大值',
        null=True,
        blank=True,
        help_text='正常范围最大值'
    )
    precision = models.IntegerField(
        verbose_name='小数位数',
        default=1,
        help_text='数据显示保留的小数位数'
    )
    is_active = models.BooleanField(
        verbose_name='是否启用',
        default=True
    )
    sort_order = models.IntegerField(
        verbose_name='排序',
        default=0
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
        db_table = 'sensor_types'
        verbose_name = '传感器类型'
        verbose_name_plural = '传感器类型'
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Device(models.Model):
    """
    设备模型
    物联网设备信息
    """
    STATUS_CHOICES = [
        ('online', '在线'),
        ('offline', '离线'),
        ('error', '故障'),
        ('maintenance', '维护中'),
    ]

    device_id = models.CharField(
        verbose_name='设备ID',
        max_length=50,
        unique=True,
        db_index=True,
        help_text='设备唯一标识符'
    )
    name = models.CharField(
        verbose_name='设备名称',
        max_length=100
    )
    location = models.CharField(
        verbose_name='安装位置',
        max_length=200,
        blank=True
    )
    description = models.CharField(
        verbose_name='描述',
        max_length=500,
        blank=True
    )
    status = models.CharField(
        verbose_name='状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='offline'
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='所有者',
        on_delete=models.SET_NULL,
        null=True,
        related_name='devices'
    )
    ip_address = models.GenericIPAddressField(
        verbose_name='IP地址',
        null=True,
        blank=True
    )
    firmware_version = models.CharField(
        verbose_name='固件版本',
        max_length=50,
        blank=True
    )
    battery_level = models.IntegerField(
        verbose_name='电池电量',
        null=True,
        blank=True,
        help_text='百分比 0-100'
    )
    last_heartbeat = models.DateTimeField(
        verbose_name='最后心跳时间',
        null=True,
        blank=True
    )
    sensor_types = models.ManyToManyField(
        SensorType,
        verbose_name='支持的传感器',
        related_name='devices',
        blank=True
    )
    is_active = models.BooleanField(
        verbose_name='是否启用',
        default=True
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
        db_table = 'devices'
        verbose_name = '设备'
        verbose_name_plural = '设备'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['owner']),
            models.Index(fields=['-last_heartbeat']),
        ]

    def __str__(self):
        return f"{self.name} ({self.device_id})"

    @property
    def is_online(self):
        """判断设备是否在线"""
        return self.status == 'online'


class DeviceLog(models.Model):
    """
    设备日志
    记录设备操作和状态变更
    """
    LOG_TYPE_CHOICES = [
        ('status', '状态变更'),
        ('control', '控制操作'),
        ('error', '错误日志'),
        ('info', '信息日志'),
    ]

    device = models.ForeignKey(
        Device,
        verbose_name='设备',
        on_delete=models.CASCADE,
        related_name='logs'
    )
    log_type = models.CharField(
        verbose_name='日志类型',
        max_length=20,
        choices=LOG_TYPE_CHOICES
    )
    message = models.TextField(
        verbose_name='日志消息'
    )
    data = models.JSONField(
        verbose_name='附加数据',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )

    class Meta:
        db_table = 'device_logs'
        verbose_name = '设备日志'
        verbose_name_plural = '设备日志'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.device.name} - {self.log_type} - {self.created_at}"
