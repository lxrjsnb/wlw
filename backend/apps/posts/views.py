"""
帖子相关API视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import TruncDate, TruncHour
from django.utils import timezone
from datetime import timedelta, datetime
from collections import defaultdict

from .models import SocialPost, PostSummary
from .serializers import (
    SocialPostSerializer,
    SocialPostListSerializer,
    PostSummarySerializer,
    PostStatsSerializer,
    SentimentAnalysisRequestSerializer,
    SentimentAnalysisResponseSerializer
)
from .services import SentimentAnalyzer, SocialDataSimulator


class SocialPostViewSet(viewsets.ReadOnlyModelViewSet):
    """帖子视图集"""
    permission_classes = [IsAuthenticated]
    filterset_fields = ['topic', 'platform', 'sentiment']
    search_fields = ['content', 'author']
    ordering_fields = ['publish_time', 'influence_score', 'likes']
    ordering = ['-publish_time']

    def get_queryset(self):
        queryset = SocialPost.objects.select_related('topic', 'platform')
        # 日期范围筛选
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(publish_time__gte=start_date)
        if end_date:
            queryset = queryset.filter(publish_time__lte=end_date)
        return queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return SocialPostListSerializer
        return SocialPostSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = SocialPostSerializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """获取帖子统计"""
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)

        # 基础统计
        queryset = SocialPost.objects.all()

        total_posts = queryset.count()
        today_posts = queryset.filter(publish_time__date=today).count()
        yesterday_posts = queryset.filter(publish_time__date=yesterday).count()

        # 情感统计
        sentiment_stats = queryset.aggregate(
            positive_count=Count('id', filter=Q(sentiment='positive')),
            neutral_count=Count('id', filter=Q(sentiment='neutral')),
            negative_count=Count('id', filter=Q(sentiment='negative')),
            avg_sentiment_score=Avg('sentiment_score'),
            avg_influence_score=Avg('influence_score')
        )

        # 平台分布
        platform_stats = queryset.values('platform__name', 'platform__color').annotate(
            count=Count('id')
        ).order_by('-count')

        platform_distribution = [
            {
                'name': stat['platform__name'],
                'value': stat['count'],
                'color': stat['platform__color']
            }
            for stat in platform_stats
        ]

        # 情感分布
        sentiment_distribution = [
            {'name': '正面', 'value': sentiment_stats['positive_count'], 'color': '#67C23A'},
            {'name': '中性', 'value': sentiment_stats['neutral_count'], 'color': '#909399'},
            {'name': '负面', 'value': sentiment_stats['negative_count'], 'color': '#F56C6C'},
        ]

        # 趋势数据（近7天）
        trend_data = []
        for i in range(7):
            date = today - timedelta(days=i)
            daily_count = queryset.filter(publish_time__date=date).count()
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'count': daily_count
            })
        trend_data.reverse()

        data = {
            'total_posts': total_posts,
            'today_posts': today_posts,
            'yesterday_posts': yesterday_posts,
            'positive_count': sentiment_stats['positive_count'] or 0,
            'neutral_count': sentiment_stats['neutral_count'] or 0,
            'negative_count': sentiment_stats['negative_count'] or 0,
            'avg_sentiment_score': round(sentiment_stats['avg_sentiment_score'] or 0, 2),
            'avg_influence_score': round(sentiment_stats['avg_influence_score'] or 0, 2),
            'platform_distribution': platform_distribution,
            'sentiment_distribution': sentiment_distribution,
            'trend_data': trend_data
        }

        serializer = PostStatsSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def sentiment_analysis(self, request):
        """情感分析"""
        serializer = SentimentAnalysisRequestSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            analyzer = SentimentAnalyzer()
            result = analyzer.analyze(text)
            response_serializer = SentimentAnalysisResponseSerializer(result)
            return Response(response_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def hot(self, request):
        """热门帖子"""
        limit = int(request.query_params.get('limit', 20))
        queryset = self.get_queryset().order_by('-influence_score')[:limit]
        serializer = SocialPostListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def positive(self, request):
        """正面帖子"""
        queryset = self.get_queryset().filter(sentiment='positive')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SocialPostListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SocialPostListSerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def negative(self, request):
        """负面帖子"""
        queryset = self.get_queryset().filter(sentiment='negative')
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = SocialPostListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SocialPostListSerializer(queryset, many=True)
        return Response(serializer.data)


class PostSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    """帖子汇总视图集"""
    queryset = PostSummary.objects.select_related('topic', 'platform')
    serializer_class = PostSummarySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['topic', 'platform', 'period']
    ordering_fields = ['date', 'post_count']
    ordering = ['-date']
