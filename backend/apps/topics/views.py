"""
话题相关API视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import Platform, Topic
from .serializers import (
    PlatformSerializer,
    TopicSerializer,
    TopicListSerializer,
    TopicStatsSerializer
)


class PlatformViewSet(viewsets.ReadOnlyModelViewSet):
    """平台视图集"""
    queryset = Platform.objects.filter(is_active=True)
    serializer_class = PlatformSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['sort_order', 'name']
    ordering = ['sort_order']


class TopicViewSet(viewsets.ModelViewSet):
    """话题视图集"""
    queryset = Topic.objects.select_related('owner').prefetch_related('platforms')
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'priority', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'priority']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return TopicListSerializer
        return TopicSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        # 只显示用户有权限的话题
        user = self.request.user
        if user.role == 'viewer':
            # 查看者只能看到已分配的话题
            queryset = queryset.filter(owner=user)
        return queryset

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取话题统计"""
        now = timezone.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        # 基础统计
        total_topics = Topic.objects.count()
        active_topics = Topic.objects.filter(status='active').count()
        paused_topics = Topic.objects.filter(status='paused').count()
        archived_topics = Topic.objects.filter(status='archived').count()
        high_priority_topics = Topic.objects.filter(priority='high', status='active').count()

        # 本周新增
        new_topics_week = Topic.objects.filter(created_at__gte=week_ago).count()

        data = {
            'total_topics': total_topics,
            'active_topics': active_topics,
            'paused_topics': paused_topics,
            'archived_topics': archived_topics,
            'high_priority_topics': high_priority_topics,
            'new_topics_week': new_topics_week,
        }

        serializer = TopicStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """暂停话题"""
        topic = self.get_object()
        topic.status = 'paused'
        topic.save()
        return Response({'message': '话题已暂停'})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活话题"""
        topic = self.get_object()
        topic.status = 'active'
        topic.save()
        return Response({'message': '话题已激活'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """归档话题"""
        topic = self.get_object()
        topic.status = 'archived'
        topic.save()
        return Response({'message': '话题已归档'})

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取活跃话题列表"""
        queryset = self.get_queryset().filter(status='active')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TopicListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TopicListSerializer(queryset, many=True)
        return Response(serializer.data)
