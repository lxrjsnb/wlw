"""
预警相关API视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import AlertRule, AlertRecord
from .serializers import (
    AlertRuleSerializer,
    AlertRuleCreateSerializer,
    AlertRecordSerializer,
    AlertRecordListSerializer,
    AlertRecordUpdateSerializer,
    AlertStatsSerializer
)
from .services import AlertChecker


class AlertRuleViewSet(viewsets.ModelViewSet):
    """预警规则视图集"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['topic', 'rule_type', 'priority', 'enabled']
    search_fields = ['topic__name', 'description']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        return AlertRule.objects.select_related('topic').prefetch_related('notify_users')

    def get_serializer_class(self):
        if self.action == 'create':
            return AlertRuleCreateSerializer
        return AlertRuleSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AlertRuleSerializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def enable(self, request, pk=None):
        """启用规则"""
        rule = self.get_object()
        rule.enabled = True
        rule.save()
        return Response({'message': '规则已启用'})

    @action(detail=True, methods=['post'])
    def disable(self, request, pk=None):
        """禁用规则"""
        rule = self.get_object()
        rule.enabled = False
        rule.save()
        return Response({'message': '规则已禁用'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取启用的规则列表"""
        queryset = self.get_queryset().filter(enabled=True)
        serializer = AlertRuleSerializer(queryset, many=True)
        return Response(serializer.data)


class AlertRecordViewSet(viewsets.ModelViewSet):
    """预警记录视图集"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['topic', 'status']
    search_fields = ['topic__name', 'message']
    ordering_fields = ['triggered_at', 'priority']
    ordering = ['-triggered_at']

    def get_queryset(self):
        return AlertRecord.objects.select_related(
            'topic', 'alert_rule', 'acknowledged_by', 'resolved_by'
        )

    def get_serializer_class(self):
        if self.action == 'list':
            return AlertRecordListSerializer
        elif self.action in ['acknowledge', 'resolve']:
            return AlertRecordUpdateSerializer
        return AlertRecordSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = AlertRecordSerializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """确认预警"""
        record = self.get_object()
        if record.status != 'pending':
            return Response(
                {'error': '只能确认待处理的预警'},
                status=status.HTTP_400_BAD_REQUEST
            )
        record.acknowledge(request.user)
        return Response({'message': '预警已确认'})

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """解决预警"""
        record = self.get_object()
        serializer = AlertRecordUpdateSerializer(data=request.data)
        if serializer.is_valid():
            note = serializer.validated_data.get('resolution_note', '')
            record.resolve(request.user, note)
            return Response({'message': '预警已解决'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """获取待处理的预警"""
        queryset = self.get_queryset().filter(status='pending')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AlertRecordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = AlertRecordListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取预警统计"""
        now = timezone.now()
        today = now.date()

        # 规则统计
        total_rules = AlertRule.objects.count()
        active_rules = AlertRule.objects.filter(enabled=True).count()

        # 记录统计
        total_records = AlertRecord.objects.count()
        pending_records = AlertRecord.objects.filter(status='pending').count()
        acknowledged_records = AlertRecord.objects.filter(status='acknowledged').count()
        resolved_records = AlertRecord.objects.filter(status='resolved').count()

        # 今日触发
        today_triggered = AlertRecord.objects.filter(triggered_at__date=today).count()

        # 高优先级待处理
        critical_pending = AlertRecord.objects.filter(
            status='pending',
            alert_rule__priority='critical'
        ).count()

        data = {
            'total_rules': total_rules,
            'active_rules': active_rules,
            'total_records': total_records,
            'pending_records': pending_records,
            'acknowledged_records': acknowledged_records,
            'resolved_records': resolved_records,
            'today_triggered': today_triggered,
            'critical_pending': critical_pending,
        }

        serializer = AlertStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def batch_acknowledge(self, request):
        """批量确认预警"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': '请提供要确认的预警ID列表'},
                status=status.HTTP_400_BAD_REQUEST
            )

        records = AlertRecord.objects.filter(
            id__in=ids,
            status='pending'
        )
        count = 0
        for record in records:
            record.acknowledge(request.user)
            count += 1

        return Response({'message': f'已确认{count}条预警'})

    @action(detail=False, methods=['post'])
    def batch_resolve(self, request):
        """批量解决预警"""
        ids = request.data.get('ids', [])
        note = request.data.get('resolution_note', '')

        if not ids:
            return Response(
                {'error': '请提供要解决的预警ID列表'},
                status=status.HTTP_400_BAD_REQUEST
            )

        records = AlertRecord.objects.filter(id__in=ids)
        count = 0
        for record in records:
            if record.status != 'resolved':
                record.resolve(request.user, note)
                count += 1

        return Response({'message': f'已解决{count}条预警'})
