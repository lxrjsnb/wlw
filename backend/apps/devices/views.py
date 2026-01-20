"""
设备模块视图
Device views for device management
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from .models import Device, SensorType, DeviceLog
from .serializers import (
    DeviceSerializer,
    DeviceCreateSerializer,
    DeviceUpdateSerializer,
    DeviceDetailSerializer,
    DeviceControlSerializer,
    SensorTypeSerializer,
    DeviceLogSerializer
)
from core.pagination import StandardPagination


class SensorTypeListView(generics.ListAPIView):
    """
    传感器类型列表
    Sensor type list
    """
    queryset = SensorType.objects.filter(is_active=True)
    serializer_class = SensorTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination


class SensorTypeDetailView(generics.RetrieveAPIView):
    """
    传感器类型详情
    Sensor type detail
    """
    queryset = SensorType.objects.all()
    serializer_class = SensorTypeSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceListView(generics.ListCreateAPIView):
    """
    设备列表/创建
    Device list/create view
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_serializer_class(self):
        """根据请求方法选择序列化器"""
        if self.request.method == 'POST':
            return DeviceCreateSerializer
        return DeviceSerializer

    def get_queryset(self):
        """过滤设备列表"""
        queryset = Device.objects.select_related('owner').prefetch_related('sensor_types')

        # 状态过滤
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # 所有者过滤
        owner_id = self.request.query_params.get('owner_id')
        if owner_id:
            queryset = queryset.filter(owner_id=owner_id)

        # 关键词搜索（设备ID、名称、位置）
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(
                Q(device_id__icontains=keyword) |
                Q(name__icontains=keyword) |
                Q(location__icontains=keyword)
            )

        # 传感器类型过滤
        sensor_type = self.request.query_params.get('sensor_type')
        if sensor_type:
            queryset = queryset.filter(sensor_types__code=sensor_type)

        # 普通用户只能看到自己的设备
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(owner=user)

        return queryset.distinct().order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """创建设备"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()

        # 记录日志
        DeviceLog.objects.create(
            device=device,
            log_type='info',
            message=f'设备创建成功，创建人: {request.user.username}'
        )

        return Response({
            'code': 0,
            'message': '设备创建成功',
            'data': DeviceSerializer(device).data
        }, status=status.HTTP_201_CREATED)


class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    设备详情/更新/删除
    Device detail/update/destroy view
    """
    queryset = Device.objects.select_related('owner').prefetch_related('sensor_types')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """根据请求方法选择序列化器"""
        if self.request.method == 'GET':
            return DeviceDetailSerializer
        elif self.request.method in ['PUT', 'PATCH']:
            return DeviceUpdateSerializer
        return DeviceSerializer

    def get_queryset(self):
        """权限过滤"""
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(owner=user)
        return queryset

    def update(self, request, *args, **kwargs):
        """更新设备"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        device = serializer.save()

        # 记录日志
        DeviceLog.objects.create(
            device=device,
            log_type='info',
            message=f'设备更新成功，操作人: {request.user.username}'
        )

        return Response({
            'code': 0,
            'message': '设备更新成功',
            'data': DeviceSerializer(device).data
        })

    def destroy(self, request, *args, **kwargs):
        """删除设备"""
        instance = self.get_object()
        device_name = instance.name

        # 记录日志
        DeviceLog.objects.create(
            device=instance,
            log_type='info',
            message=f'设备删除成功，操作人: {request.user.username}'
        )

        instance.delete()

        return Response({
            'code': 0,
            'message': f'设备 {device_name} 已删除',
            'data': None
        })


class DeviceControlView(APIView):
    """
    设备控制视图
    Device control view
    """
    permission_classes = [permissions.IsAuthenticated]
    from core.permissions import CanControlDevice
    permission_classes = [CanControlDevice]

    def post(self, request, device_id):
        """
        远程控制设备

        Args:
            request: 请求对象
            device_id: 设备ID

        Returns:
            Response: 控制结果
        """
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({
                'code': 404,
                'message': '设备不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        # 检查设备状态
        if not device.is_online:
            return Response({
                'code': 400,
                'message': '设备离线，无法控制',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 验证控制命令
        serializer = DeviceControlSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        command = serializer.validated_data['command']
        parameters = serializer.validated_data.get('parameters', {})

        # TODO: 通过MQTT发送控制命令到设备
        # 这里需要实现MQTT发布逻辑

        # 记录控制日志
        DeviceLog.objects.create(
            device=device,
            log_type='control',
            message=f'发送控制命令: {command}',
            data={
                'command': command,
                'parameters': parameters,
                'operator': request.user.username
            }
        )

        return Response({
            'code': 0,
            'message': f'控制命令 {command} 已发送',
            'data': {
                'command': command,
                'parameters': parameters,
                'device_id': device.device_id
            }
        })


class DeviceLogListView(generics.ListAPIView):
    """
    设备日志列表
    Device log list
    """
    serializer_class = DeviceLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """获取设备日志"""
        device_id = self.kwargs.get('device_id')

        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return DeviceLog.objects.none()

        # 权限检查
        user = self.request.user
        if user.role == 'viewer' and device.owner != user:
            return DeviceLog.objects.none()

        queryset = DeviceLog.objects.filter(device=device)

        # 日志类型过滤
        log_type = self.request.query_params.get('log_type')
        if log_type:
            queryset = queryset.filter(log_type=log_type)

        return queryset.order_by('-created_at')


class DeviceStatsView(APIView):
    """
    设备统计视图
    Device statistics view
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        获取设备统计信息

        Args:
            request: 请求对象

        Returns:
            Response: 统计信息
        """
        queryset = Device.objects.all()
        user = request.user

        # 普通用户只能看到自己的设备
        if user.role == 'viewer':
            queryset = queryset.filter(owner=user)

        # 总数统计
        total_count = queryset.count()

        # 状态统计
        online_count = queryset.filter(status='online').count()
        offline_count = queryset.filter(status='offline').count()
        error_count = queryset.filter(status='error').count()
        maintenance_count = queryset.filter(status='maintenance').count()

        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'total': total_count,
                'online': online_count,
                'offline': offline_count,
                'error': error_count,
                'maintenance': maintenance_count,
                'online_rate': round(online_count / total_count * 100, 2) if total_count > 0 else 0
            }
        })
