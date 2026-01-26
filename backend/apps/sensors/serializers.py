"""
传感器数据模块序列化器
Sensor data serializers for data management
"""
from rest_framework import serializers
from .models import SensorData, SensorDataSummary
from apps.devices.serializers import DeviceSerializer, SensorTypeSerializer


class SensorDataSerializer(serializers.ModelSerializer):
    """
    传感器数据序列化器
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    device_id_str = serializers.CharField(source='device.device_id', read_only=True)
    sensor_type_name = serializers.CharField(source='sensor_type.name', read_only=True)
    sensor_type_code = serializers.CharField(source='sensor_type.code', read_only=True)
    precision = serializers.IntegerField(source='sensor_type.precision', read_only=True)

    class Meta:
        model = SensorData
        fields = [
            'id', 'device', 'device_name', 'device_id_str',
            'sensor_type', 'sensor_type_name', 'sensor_type_code',
            'value', 'unit', 'timestamp', 'quality',
            'extra_data', 'created_at', 'precision'
        ]
        read_only_fields = ['id', 'created_at']

    def to_representation(self, instance):
        """格式化数值显示"""
        data = super().to_representation(instance)
        precision = instance.sensor_type.precision
        if precision is not None:
            data['value'] = round(instance.value, precision)
        return data


class SensorDataCreateSerializer(serializers.ModelSerializer):
    """
    传感器数据创建序列化器（MQTT上报使用）
    """
    device_id_str = serializers.CharField(write_only=True, help_text='设备ID')
    sensor_type_code = serializers.CharField(write_only=True, help_text='传感器类型代码')

    class Meta:
        model = SensorData
        fields = ['device_id_str', 'sensor_type_code', 'value', 'timestamp', 'quality', 'extra_data']

    def validate(self, attrs):
        """验证设备ID和传感器类型"""
        from apps.devices.models import Device, SensorType

        device_id = attrs.get('device_id_str')
        sensor_code = attrs.get('sensor_type_code')

        try:
            device = Device.objects.get(device_id=device_id)
            attrs['device'] = device
        except Device.DoesNotExist:
            raise serializers.ValidationError({'device_id_str': '设备不存在'})

        try:
            sensor_type = SensorType.objects.get(code=sensor_code)
            attrs['sensor_type'] = sensor_type
            attrs['unit'] = sensor_type.unit
        except SensorType.DoesNotExist:
            raise serializers.ValidationError({'sensor_type_code': '传感器类型不存在'})

        # 验证数值范围
        value = attrs.get('value')
        if sensor_type.min_value is not None and value < sensor_type.min_value:
            raise serializers.ValidationError({'value': f'数值不能小于 {sensor_type.min_value}'})
        if sensor_type.max_value is not None and value > sensor_type.max_value:
            raise serializers.ValidationError({'value': f'数值不能大于 {sensor_type.max_value}'})

        return attrs

    def create(self, validated_data):
        """创建传感器数据"""
        validated_data.pop('device_id_str')
        validated_data.pop('sensor_type_code')
        return SensorData.objects.create(**validated_data)


class SensorDataBatchSerializer(serializers.Serializer):
    """
    批量创建传感器数据序列化器
    """
    device_id_str = serializers.CharField(help_text='设备ID')
    data = serializers.JSONField(help_text='传感器数据字典，格式: {sensor_code: value}')

    def validate_data(self, value):
        """验证数据格式"""
        if not isinstance(value, dict):
            raise serializers.ValidationError('数据必须是字典格式')
        return value


class SensorDataStatisticsSerializer(serializers.Serializer):
    """
    传感器数据统计序列化器
    """
    device_id = serializers.CharField(required=False)  # device_id 从URL路径获取，不需要在query参数中传递
    sensor_type = serializers.CharField(required=True)
    start_time = serializers.DateTimeField(required=True)
    end_time = serializers.DateTimeField(required=True)


class SensorDataSummarySerializer(serializers.ModelSerializer):
    """
    传感器数据汇总序列化器
    """
    device_name = serializers.CharField(source='device.name', read_only=True)
    sensor_type_name = serializers.CharField(source='sensor_type.name', read_only=True)
    sensor_type_code = serializers.CharField(source='sensor_type.code', read_only=True)
    unit = serializers.CharField(source='sensor_type.unit', read_only=True)

    class Meta:
        model = SensorDataSummary
        fields = [
            'id', 'device', 'device_name',
            'sensor_type', 'sensor_type_name', 'sensor_type_code',
            'summary_type', 'time_start', 'time_end',
            'avg_value', 'min_value', 'max_value', 'count', 'unit'
        ]
        read_only_fields = ['id']
