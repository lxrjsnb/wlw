"""
传感器数据模块视图
Sensor data views for data management
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from django.db.models import Avg, Min, Max, Count
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
from django.http import HttpResponse
from django.conf import settings
import csv
import json

from .models import SensorData, SensorDataSummary
from .serializers import (
    SensorDataSerializer,
    SensorDataCreateSerializer,
    SensorDataBatchSerializer,
    SensorDataSummarySerializer,
    SensorDataStatisticsSerializer
)
from apps.devices.models import Device
from core.pagination import StandardPagination


class SensorDataListView(ListAPIView):
    """
    传感器数据列表
    Sensor data list with filtering
    """
    serializer_class = SensorDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """过滤传感器数据"""
        queryset = SensorData.objects.select_related('device', 'sensor_type')

        # 设备过滤
        device_id = self.request.query_params.get('device_id')
        if device_id:
            try:
                device = Device.objects.get(device_id=device_id)
                queryset = queryset.filter(device=device)
            except Device.DoesNotExist:
                return SensorData.objects.none()

        # 传感器类型过滤
        sensor_type = self.request.query_params.get('sensor_type')
        if sensor_type:
            queryset = queryset.filter(sensor_type__code=sensor_type)

        # 时间范围过滤
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')

        if start_time:
            try:
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=start_time)
            except ValueError:
                pass

        if end_time:
            try:
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=end_time)
            except ValueError:
                pass

        # 数据质量过滤
        quality = self.request.query_params.get('quality')
        if quality:
            queryset = queryset.filter(quality=quality)

        # 权限检查
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(device__owner=user)

        return queryset.order_by('-timestamp')


class SensorDataCreateView(APIView):
    """
    创建传感器数据
    Create sensor data (for MQTT usage)
    """
    permission_classes = [permissions.AllowAny]  # MQTT设备可能没有JWT

    def post(self, request):
        """创建单条传感器数据"""
        serializer = SensorDataCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sensor_data = serializer.save()

        return Response({
            'code': 0,
            'message': '数据创建成功',
            'data': SensorDataSerializer(sensor_data).data
        }, status=status.HTTP_201_CREATED)


class SensorDataBatchCreateView(APIView):
    """
    批量创建传感器数据
    Batch create sensor data
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """批量创建传感器数据"""
        serializer = SensorDataBatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_id = serializer.validated_data['device_id_str']
        data_dict = serializer.validated_data['data']

        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({
                'code': 404,
                'message': '设备不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        # 批量创建数据
        from apps.devices.models import SensorType
        created_data = []
        timestamp = timezone.now()

        for sensor_code, value in data_dict.items():
            try:
                sensor_type = SensorType.objects.get(code=sensor_code)

                # 创建数据记录
                sensor_data = SensorData.objects.create(
                    device=device,
                    sensor_type=sensor_type,
                    value=float(value),
                    unit=sensor_type.unit,
                    timestamp=timestamp,
                    quality='good'
                )
                created_data.append(sensor_data)
            except SensorType.DoesNotExist:
                continue

        return Response({
            'code': 0,
            'message': f'成功创建 {len(created_data)} 条数据',
            'data': {
                'count': len(created_data),
                'device_id': device_id,
                'timestamp': timestamp
            }
        }, status=status.HTTP_201_CREATED)


class SensorDataLatestView(APIView):
    """
    获取设备最新数据
    Get latest sensor data for device
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, device_id):
        """
        获取设备最新传感器数据

        Args:
            request: 请求对象
            device_id: 设备ID

        Returns:
            Response: 最新数据
        """
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({
                'code': 404,
                'message': '设备不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        # 权限检查
        user = request.user
        if user.role == 'viewer' and device.owner != user:
            return Response({
                'code': 403,
                'message': '无权访问该设备数据',
                'data': None
            }, status=status.HTTP_403_FORBIDDEN)

        # 获取最新数据
        queryset = SensorData.objects.filter(device=device).select_related('sensor_type')

        # 按传感器类型分组获取最新一条
        sensor_codes = set(queryset.values_list('sensor_type__code', flat=True))
        latest_data = []

        for code in sensor_codes:
            latest = queryset.filter(sensor_type__code=code).order_by('-timestamp').first()
            if latest:
                latest_data.append(latest)

        serializer = SensorDataSerializer(latest_data, many=True)

        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'device_id': device_id,
                'device_name': device.name,
                'data': serializer.data
            }
        })


class SensorDataStatisticsView(APIView):
    """
    传感器数据统计
    Get sensor data statistics
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, device_id):
        """
        获取设备传感器数据统计

        Args:
            request: 请求对象
            device_id: 设备ID

        Returns:
            Response: 统计信息
        """
        serializer = SensorDataStatisticsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({
                'code': 404,
                'message': '设备不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        sensor_code = serializer.validated_data['sensor_type']
        start_time = serializer.validated_data['start_time']
        end_time = serializer.validated_data['end_time']

        # 获取统计数据
        queryset = SensorData.objects.filter(
            device=device,
            sensor_type__code=sensor_code,
            timestamp__range=(start_time, end_time)
        )

        stats = queryset.aggregate(
            count=Count('id'),
            min_value=Min('value'),
            max_value=Max('value'),
            avg_value=Avg('value')
        )

        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'device_id': device_id,
                'sensor_type': sensor_code,
                'start_time': start_time,
                'end_time': end_time,
                'count': stats['count'],
                'min': stats['min_value'],
                'max': stats['max_value'],
                'avg': round(stats['avg_value'], 2) if stats['avg_value'] else None
            }
        })


class SensorDataExportView(APIView):
    """
    传感器数据导出
    Export sensor data to CSV/Excel
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """导出传感器数据"""
        # 获取查询参数
        device_id = request.query_params.get('device_id')
        sensor_type = request.query_params.get('sensor_type')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')
        export_format = request.query_params.get('format', 'csv')

        # 构建查询
        queryset = SensorData.objects.select_related('device', 'sensor_type')

        if device_id:
            try:
                device = Device.objects.get(device_id=device_id)
                queryset = queryset.filter(device=device)
            except Device.DoesNotExist:
                return Response({
                    'code': 404,
                    'message': '设备不存在',
                    'data': None
                }, status=status.HTTP_404_NOT_FOUND)

        if sensor_type:
            queryset = queryset.filter(sensor_type__code=sensor_type)

        if start_time:
            try:
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__gte=start_time)
            except ValueError:
                pass

        if end_time:
            try:
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                queryset = queryset.filter(timestamp__lte=end_time)
            except ValueError:
                pass

        # 权限检查
        user = request.user
        if user.role == 'viewer':
            queryset = queryset.filter(device__owner=user)

        # 限制导出数量
        queryset = queryset.order_by('-timestamp')[:10000]

        # 转换为DataFrame
        data = queryset.values(
            'device__device_id',
            'device__name',
            'sensor_type__name',
            'sensor_type__code',
            'value',
            'unit',
            'timestamp',
            'quality'
        )
        df = pd.DataFrame(list(data))

        if df.empty:
            return Response({
                'code': 400,
                'message': '没有数据可导出',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # CSV导出
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="sensor_data.csv"'
            df.to_csv(response, index=False, encoding='utf-8-sig')
            return response

        # Excel导出
        elif export_format == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="sensor_data.xlsx"'
            with pd.ExcelWriter(response, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            return response

        else:
            return Response({
                'code': 400,
                'message': '不支持的导出格式',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)


class SensorDataHistoryView(APIView):
    """
    获取历史数据（用于图表展示）
    Get historical data for charts
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, device_id):
        """
        获取历史数据

        Args:
            request: 请求对象
            device_id: 设备ID

        Returns:
            Response: 历史数据
        """
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({
                'code': 404,
                'message': '设备不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        # 获取参数
        sensor_code = request.query_params.get('sensor_type')
        hours = int(request.query_params.get('hours', 24))

        # 计算时间范围
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)

        # 查询数据
        queryset = SensorData.objects.filter(
            device=device,
            timestamp__range=(start_time, end_time)
        )

        if sensor_code:
            queryset = queryset.filter(sensor_type__code=sensor_code)

        queryset = queryset.order_by('timestamp')

        # 序列化
        serializer = SensorDataSerializer(queryset, many=True)

        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'device_id': device_id,
                'sensor_type': sensor_code,
                'start_time': start_time,
                'end_time': end_time,
                'count': queryset.count(),
                'data': serializer.data
            }
        })
