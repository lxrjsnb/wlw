"""
传感器数据模型
Sensor data models for storing IoT measurements
"""
from django.db import models
from django.conf import settings
from apps.devices.models import Device, SensorType


class SensorData(models.Model):
    """
    传感器数据
    存储设备上报的传感器测量数据
    """
    device = models.ForeignKey(
        Device,
        verbose_name='设备',
        on_delete=models.CASCADE,
        related_name='sensor_data',
        db_index=True
    )
    sensor_type = models.ForeignKey(
        SensorType,
        verbose_name='传感器类型',
        on_delete=models.PROTECT,
        related_name='data_records',
        db_index=True
    )
    value = models.FloatField(
        verbose_name='数值'
    )
    unit = models.CharField(
        verbose_name='单位',
        max_length=10
    )
    timestamp = models.DateTimeField(
        verbose_name='时间戳',
        db_index=True
    )
    quality = models.CharField(
        verbose_name='数据质量',
        max_length=20,
        choices=[
            ('good', '良好'),
            ('uncertain', '不确定'),
            ('bad', '差'),
        ],
        default='good'
    )
    extra_data = models.JSONField(
        verbose_name='额外数据',
        null=True,
        blank=True,
        help_text='存储额外的传感器信息'
    )
    created_at = models.DateTimeField(
        verbose_name='接收时间',
        auto_now_add=True
    )

    class Meta:
        db_table = 'sensor_data'
        verbose_name = '传感器数据'
        verbose_name_plural = '传感器数据'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', 'timestamp']),
            models.Index(fields=['sensor_type', 'timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        # 复合索引：设备+时间
        # models.Index(fields=['device_id', 'timestamp'], name='idx_device_time'),

    def __str__(self):
        return f"{self.device.name} - {self.sensor_type.name}: {self.value}{self.unit} @ {self.timestamp}"

    @classmethod
    def get_latest_data(cls, device_id, sensor_type=None):
        """
        获取设备的最新数据

        Args:
            device_id: 设备ID
            sensor_type: 传感器类型（可选）

        Returns:
            SensorData or None
        """
        queryset = cls.objects.filter(device_id=device_id)
        if sensor_type:
            queryset = queryset.filter(sensor_type__code=sensor_type)
        return queryset.order_by('-timestamp').first()

    @classmethod
    def get_statistics(cls, device_id, sensor_type, start_time, end_time):
        """
        获取数据统计信息

        Args:
            device_id: 设备ID
            sensor_type: 传感器类型
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            dict: 统计信息
        """
        queryset = cls.objects.filter(
            device_id=device_id,
            sensor_type__code=sensor_type,
            timestamp__range=(start_time, end_time)
        )

        return {
            'count': queryset.count(),
            'min': queryset.aggregate(min_value=models.Min('value'))['min_value'],
            'max': queryset.aggregate(max_value=models.Max('value'))['max_value'],
            'avg': queryset.aggregate(avg_value=models.Avg('value'))['avg_value'],
        }


class SensorDataSummary(models.Model):
    """
    传感器数据汇总
    按小时/天聚合的数据，用于历史数据查询优化
    """
    SUMMARY_TYPE_CHOICES = [
        ('hour', '小时'),
        ('day', '天'),
        ('week', '周'),
        ('month', '月'),
    ]

    device = models.ForeignKey(
        Device,
        verbose_name='设备',
        on_delete=models.CASCADE,
        related_name='data_summaries'
    )
    sensor_type = models.ForeignKey(
        SensorType,
        verbose_name='传感器类型',
        on_delete=models.PROTECT,
        related_name='data_summaries'
    )
    summary_type = models.CharField(
        verbose_name='汇总类型',
        max_length=10,
        choices=SUMMARY_TYPE_CHOICES
    )
    time_start = models.DateTimeField(
        verbose_name='汇总起始时间',
        db_index=True
    )
    time_end = models.DateTimeField(
        verbose_name='汇总结束时间'
    )
    avg_value = models.FloatField(
        verbose_name='平均值'
    )
    min_value = models.FloatField(
        verbose_name='最小值'
    )
    max_value = models.FloatField(
        verbose_name='最大值'
    )
    count = models.IntegerField(
        verbose_name='数据点数'
    )
    created_at = models.DateTimeField(
        verbose_name='创建时间',
        auto_now_add=True
    )

    class Meta:
        db_table = 'sensor_data_summary'
        verbose_name = '传感器数据汇总'
        verbose_name_plural = '传感器数据汇总'
        ordering = ['-time_start']
        unique_together = ['device', 'sensor_type', 'summary_type', 'time_start']
        indexes = [
            models.Index(fields=['device', 'sensor_type', 'time_start']),
            models.Index(fields=['time_start']),
        ]

    def __str__(self):
        return f"{self.device.name} - {self.sensor_type.name} - {self.summary_type}: {self.time_start}"
