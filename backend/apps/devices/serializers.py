"""
设备模块序列化器
Device serializers for device management
"""
from rest_framework import serializers
from .models import Device, SensorType, DeviceLog


class SensorTypeSerializer(serializers.ModelSerializer):
    """
    传感器类型序列化器
    """
    class Meta:
        model = SensorType
        fields = ['id', 'name', 'code', 'unit', 'category',
                  'description', 'icon', 'color', 'min_value',
                  'max_value', 'precision', 'is_active', 'sort_order']
        read_only_fields = ['id']


class DeviceLogSerializer(serializers.ModelSerializer):
    """
    设备日志序列化器
    """
    device_name = serializers.CharField(source='device.name', read_only=True)

    class Meta:
        model = DeviceLog
        fields = ['id', 'device', 'device_name', 'log_type', 'message',
                  'data', 'created_at']
        read_only_fields = ['id', 'created_at']


class DeviceSerializer(serializers.ModelSerializer):
    """
    设备序列化器
    """
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    sensor_types_info = SensorTypeSerializer(
        source='sensor_types',
        many=True,
        read_only=True
    )
    is_online = serializers.BooleanField(read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'device_id', 'name', 'location', 'description',
            'status', 'owner', 'owner_name', 'owner_email',
            'ip_address', 'firmware_version', 'battery_level',
            'last_heartbeat', 'sensor_types', 'sensor_types_info',
            'is_online', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_heartbeat']

    def validate_device_id(self, value):
        """验证设备ID唯一性"""
        if self.instance:
            # 更新时排除当前设备
            if Device.objects.filter(device_id=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError('该设备ID已存在')
        else:
            # 创建时检查唯一性
            if Device.objects.filter(device_id=value).exists():
                raise serializers.ValidationError('该设备ID已存在')
        return value


class DeviceCreateSerializer(serializers.ModelSerializer):
    """
    设备创建序列化器（简化版）
    """
    sensor_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text='传感器类型ID列表'
    )

    class Meta:
        model = Device
        fields = [
            'device_id', 'name', 'location', 'description',
            'status', 'owner', 'ip_address', 'firmware_version',
            'sensor_type_ids'
        ]

    def create(self, validated_data):
        """创建设备"""
        sensor_type_ids = validated_data.pop('sensor_type_ids', [])
        device = Device.objects.create(**validated_data)

        # 添加传感器类型关联
        if sensor_type_ids:
            device.sensor_types.set(sensor_type_ids)

        return device

    def to_representation(self, instance):
        """返回完整的设备信息"""
        return DeviceSerializer(instance).data


class DeviceUpdateSerializer(serializers.ModelSerializer):
    """
    设备更新序列化器
    """
    sensor_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Device
        fields = [
            'name', 'location', 'description', 'status',
            'owner', 'ip_address', 'firmware_version',
            'battery_level', 'is_active', 'sensor_type_ids'
        ]

    def update(self, instance, validated_data):
        """更新设备"""
        sensor_type_ids = validated_data.pop('sensor_type_ids', None)

        # 更新设备基本信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 更新传感器类型关联
        if sensor_type_ids is not None:
            instance.sensor_types.set(sensor_type_ids)

        return instance

    def to_representation(self, instance):
        """返回完整的设备信息"""
        return DeviceSerializer(instance).data


class DeviceControlSerializer(serializers.Serializer):
    """
    设备控制序列化器
    """
    command = serializers.CharField(
        max_length=100,
        error_messages={'required': '控制命令不能为空'}
    )
    parameters = serializers.JSONField(
        required=False,
        help_text='命令参数'
    )

    def validate_command(self, value):
        """验证控制命令"""
        valid_commands = ['start', 'stop', 'restart', 'configure', 'calibrate']
        if value not in valid_commands:
            raise serializers.ValidationError(
                f'无效的命令，支持的命令: {", ".join(valid_commands)}'
            )
        return value


class DeviceDetailSerializer(DeviceSerializer):
    """
    设备详情序列化器（包含更多信息）
    """
    logs = DeviceLogSerializer(many=True, read_only=True, source='logs.all'[:10])

    class Meta(DeviceSerializer.Meta):
        fields = DeviceSerializer.Meta.fields + ['logs']
