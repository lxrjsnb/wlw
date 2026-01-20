"""
告警模块视图
Alarm views for alarm management
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta

from .models import AlarmRule, AlarmRecord, AlarmNotification
from .serializers import (
    AlarmRuleSerializer,
    AlarmRuleCreateSerializer,
    AlarmRecordSerializer,
    AlarmRecordUpdateSerializer,
    AlarmNotificationSerializer
)
from apps.devices.models import Device
from core.pagination import StandardPagination


class AlarmRuleListView(ListAPIView):
    """
    告警规则列表
    Alarm rule list
    """
    serializer_class = AlarmRuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """过滤告警规则"""
        queryset = AlarmRule.objects.select_related('device', 'sensor_type', 'created_by')

        # 设备过滤
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)

        # 优先级过滤
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # 启用状态过滤
        enabled = self.request.query_params.get('enabled')
        if enabled is not None:
            queryset = queryset.filter(enabled=enabled.lower() == 'true')

        # 权限检查
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(device__owner=user)

        return queryset.order_by('-priority', '-created_at')


class AlarmRuleCreateView(APIView):
    """
    创建告警规则
    Create alarm rule
    """
    permission_classes = [permissions.IsAuthenticated]
    from core.permissions import CanManageAlarms
    permission_classes = [CanManageAlarms]

    def post(self, request):
        """创建告警规则"""
        serializer = AlarmRuleCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        alarm_rule = serializer.save()

        return Response({
            'code': 0,
            'message': '告警规则创建成功',
            'data': AlarmRuleSerializer(alarm_rule).data
        }, status=status.HTTP_201_CREATED)


class AlarmRuleDetailView(RetrieveUpdateDestroyAPIView):
    """
    告警规则详情
    Alarm rule detail/update/destroy
    """
    queryset = AlarmRule.objects.select_related('device', 'sensor_type', 'created_by')
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """根据请求方法选择序列化器"""
        if self.request.method in ['PUT', 'PATCH']:
            return AlarmRuleCreateSerializer
        return AlarmRuleSerializer

    def get_queryset(self):
        """权限过滤"""
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(device__owner=user)
        return queryset


class AlarmRecordListView(ListAPIView):
    """
    告警记录列表
    Alarm record list
    """
    serializer_class = AlarmRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """过滤告警记录"""
        queryset = AlarmRecord.objects.select_related(
            'device', 'alarm_rule', 'sensor_type',
            'acknowledged_by', 'resolved_by'
        )

        # 设备过滤
        device_id = self.request.query_params.get('device_id')
        if device_id:
            queryset = queryset.filter(device__device_id=device_id)

        # 状态过滤
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # 优先级过滤
        priority = self.request.query_params.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # 传感器类型过滤
        sensor_type = self.request.query_params.get('sensor_type')
        if sensor_type:
            queryset = queryset.filter(sensor_type__code=sensor_type)

        # 时间范围过滤
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')

        if start_time:
            try:
                from datetime import datetime
                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                queryset = queryset.filter(triggered_at__gte=start_time)
            except ValueError:
                pass

        if end_time:
            try:
                from datetime import datetime
                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                queryset = queryset.filter(triggered_at__lte=end_time)
            except ValueError:
                pass

        # 权限检查
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(device__owner=user)

        return queryset.order_by('-triggered_at')


class AlarmRecordDetailView(RetrieveUpdateDestroyAPIView):
    """
    告警记录详情
    Alarm record detail/update
    """
    queryset = AlarmRecord.objects.select_related(
        'device', 'alarm_rule', 'sensor_type',
        'acknowledged_by', 'resolved_by'
    )
    permission_classes = [permissions.IsAuthenticated]
    from core.permissions import CanManageAlarms
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        """根据请求方法选择序列化器"""
        if self.request.method in ['PUT', 'PATCH']:
            return AlarmRecordUpdateSerializer
        return AlarmRecordSerializer

    def get_queryset(self):
        """权限过滤"""
        queryset = super().get_queryset()
        user = self.request.user
        if user.role == 'viewer':
            queryset = queryset.filter(device__owner=user)
        return queryset

    def update(self, request, *args, **kwargs):
        """更新告警记录"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        alarm_record = serializer.save()

        return Response({
            'code': 0,
            'message': '告警记录更新成功',
            'data': AlarmRecordSerializer(alarm_record).data
        })


class AlarmRecordResolveView(APIView):
    """
    处理告警
    Resolve alarm record
    """
    permission_classes = [permissions.IsAuthenticated]
    from core.permissions import CanManageAlarms

    def post(self, request, pk):
        """
        处理告警

        Args:
            request: 请求对象
            pk: 告警记录ID

        Returns:
            Response: 处理结果
        """
        try:
            alarm_record = AlarmRecord.objects.get(pk=pk)
        except AlarmRecord.DoesNotExist:
            return Response({
                'code': 404,
                'message': '告警记录不存在',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        # 检查状态
        if alarm_record.status == 'resolved':
            return Response({
                'code': 400,
                'message': '告警已解决',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 获取处理状态
        alarm_status = request.data.get('status', 'resolved')
        resolution_note = request.data.get('resolution_note', '')

        if alarm_status not in ['resolved', 'acknowledged', 'false_positive']:
            return Response({
                'code': 400,
                'message': '无效的状态',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # 更新告警记录
        if alarm_status == 'acknowledged':
            alarm_record.acknowledged_by = request.user
            alarm_record.acknowledged_at = timezone.now()
        else:
            alarm_record.resolved_by = request.user
            alarm_record.resolved_at = timezone.now()
            alarm_record.status = alarm_status
            alarm_record.resolution_note = resolution_note

        alarm_record.save()

        return Response({
            'code': 0,
            'message': '告警处理成功',
            'data': AlarmRecordSerializer(alarm_record).data
        })


class AlarmStatsView(APIView):
    """
    告警统计视图
    Alarm statistics view
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        获取告警统计信息

        Args:
            request: 请求对象

        Returns:
            Response: 统计信息
        """
        queryset = AlarmRecord.objects.all()
        user = request.user

        # 权限过滤
        if user.role == 'viewer':
            queryset = queryset.filter(device__owner=user)

        # 总数统计
        total_count = queryset.count()

        # 状态统计
        pending_count = queryset.filter(status='pending').count()
        acknowledged_count = queryset.filter(status='acknowledged').count()
        resolved_count = queryset.filter(status='resolved').count()

        # 优先级统计
        critical_count = queryset.filter(priority='critical', status='pending').count()
        high_count = queryset.filter(priority='high', status='pending').count()
        medium_count = queryset.filter(priority='medium', status='pending').count()

        # 24小时告警趋势
        time_24h_ago = timezone.now() - timedelta(hours=24)
        recent_alarms = queryset.filter(triggered_at__gte=time_24h_ago)
        recent_count = recent_alarms.count()

        # 获取待处理的严重告警
        critical_pending = AlarmRecord.objects.filter(
            priority='critical',
            status='pending'
        ).select_related('device', 'sensor_type')[:10]

        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'total': total_count,
                'by_status': {
                    'pending': pending_count,
                    'acknowledged': acknowledged_count,
                    'resolved': resolved_count,
                },
                'by_priority': {
                    'critical': critical_count,
                    'high': high_count,
                    'medium': medium_count,
                },
                'recent_24h': recent_count,
                'critical_pending': AlarmRecordSerializer(critical_pending, many=True).data
            }
        })


class AlarmNotificationListView(ListAPIView):
    """
    告警通知列表
    Alarm notification list
    """
    serializer_class = AlarmNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        """过滤告警通知"""
        queryset = AlarmNotification.objects.select_related('alarm_record__device')

        # 告警记录过滤
        alarm_id = self.request.query_params.get('alarm_id')
        if alarm_id:
            queryset = queryset.filter(alarm_record_id=alarm_id)

        # 状态过滤
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)

        # 通知类型过滤
        notification_type = self.request.query_params.get('notification_type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        return queryset.order_by('-created_at')
