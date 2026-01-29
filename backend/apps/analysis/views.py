"""
分析相关API视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q, Avg, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime
from collections import Counter
import json

from .models import AnalysisLog, KeywordTrend, InfluenceRanking, SentimentSnapshot
from .serializers import (
    AnalysisLogSerializer,
    KeywordTrendSerializer,
    InfluenceRankingSerializer,
    SentimentSnapshotSerializer,
    KeywordCloudSerializer,
    TrendAnalysisSerializer,
    PlatformCompareSerializer
)
from apps.posts.models import SocialPost
from apps.topics.models import Topic, Platform


class AnalysisViewSet(viewsets.GenericViewSet):
    """分析视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def keyword_cloud(self, request):
        """获取关键词云"""
        topic_id = request.query_params.get('topic_id')
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 50))

        # 计算时间范围
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # 获取帖子
        queryset = SocialPost.objects.filter(
            publish_time__gte=start_date,
            publish_time__lte=end_date
        )

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        # 提取关键词
        keywords_counter = Counter()
        for post in queryset:
            if post.keywords:
                keywords_counter.update(post.keywords)

        # 构建关键词云数据
        keyword_cloud = [
            {
                'name': keyword,
                'value': count
            }
            for keyword, count in keywords_counter.most_common(limit)
        ]

        serializer = KeywordCloudSerializer({'keywords': keyword_cloud})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def trend(self, request):
        """趋势分析"""
        topic_id = request.query_params.get('topic_id')
        days = int(request.query_params.get('days', 7))

        # 计算时间范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 获取帖子
        queryset = SocialPost.objects.filter(
            publish_time__date__gte=start_date,
            publish_time__date__lte=end_date
        )

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        # 按日期分组统计
        daily_stats = {}
        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            daily_stats[date.strftime('%Y-%m-%d')] = {
                'count': 0,
                'sentiment_score': 0,
                'influence_score': 0
            }

        # 统计每日数据
        for post in queryset:
            date_str = post.publish_time.strftime('%Y-%m-%d')
            if date_str in daily_stats:
                daily_stats[date_str]['count'] += 1
                if post.sentiment_score:
                    daily_stats[date_str]['sentiment_score'] += post.sentiment_score
                daily_stats[date_str]['influence_score'] += post.influence_score

        # 计算平均值
        dates = []
        post_counts = []
        sentiment_scores = []
        influence_scores = []

        for date_str in sorted(daily_stats.keys()):
            stats = daily_stats[date_str]
            dates.append(date_str)
            post_counts.append(stats['count'])

            if stats['count'] > 0:
                sentiment_scores.append(
                    round(stats['sentiment_score'] / stats['count'], 2)
                )
                influence_scores.append(
                    round(stats['influence_score'] / stats['count'], 2)
                )
            else:
                sentiment_scores.append(0)
                influence_scores.append(0)

        data = {
            'dates': dates,
            'post_counts': post_counts,
            'sentiment_scores': sentiment_scores,
            'influence_scores': influence_scores
        }

        serializer = TrendAnalysisSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def influence_ranking(self, request):
        """影响力排行"""
        topic_id = request.query_params.get('topic_id')
        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))

        # 计算时间范围
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # 获取帖子
        queryset = SocialPost.objects.filter(
            publish_time__gte=start_date,
            publish_time__lte=end_date
        )

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        # 热门帖子
        top_posts = list(queryset.order_by('-influence_score')[:limit].values(
            'id', 'content', 'author', 'influence_score', 'platform__name'
        ))

        # 热门作者
        top_authors = list(queryset.values('author').annotate(
            total_posts=Count('id'),
            avg_influence=Avg('influence_score')
        ).order_by('-avg_influence')[:limit])

        # 平台分布
        platform_stats = list(queryset.values('platform__name').annotate(
            count=Count('id')
        ).order_by('-count'))

        data = {
            'top_posts': top_posts,
            'top_authors': top_authors,
            'platforms': platform_stats
        }

        return Response(data)

    @action(detail=False, methods=['get'])
    def platform_compare(self, request):
        """平台对比分析"""
        topic_id = request.query_params.get('topic_id')
        days = int(request.query_params.get('days', 7))

        # 计算时间范围
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # 获取帖子
        queryset = SocialPost.objects.filter(
            publish_time__gte=start_date,
            publish_time__lte=end_date
        )

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        # 按平台统计
        platform_stats = queryset.values('platform__name', 'platform__color').annotate(
            post_count=Count('id'),
            avg_sentiment=Avg('sentiment_score'),
            total_engagement=Sum('likes') + Sum('comments') + Sum('shares')
        ).order_by('-post_count')

        platforms = []
        post_counts = []
        sentiment_scores = []
        engagement_rates = []

        for stat in platform_stats:
            platforms.append(stat['platform__name'])
            post_counts.append(stat['post_count'])
            sentiment_scores.append(round(stat['avg_sentiment'] or 0, 2))

            # 计算互动率
            if stat['post_count'] > 0:
                engagement_rate = round(stat['total_engagement'] / stat['post_count'], 2)
            else:
                engagement_rate = 0
            engagement_rates.append(engagement_rate)

        data = {
            'platforms': platforms,
            'post_counts': post_counts,
            'sentiment_scores': sentiment_scores,
            'engagement_rates': engagement_rates
        }

        serializer = PlatformCompareSerializer(data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def sentiment_timeline(self, request):
        """情感时间线"""
        topic_id = request.query_params.get('topic_id')
        days = int(request.query_params.get('days', 7))

        # 计算时间范围
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # 获取帖子
        queryset = SocialPost.objects.filter(
            publish_time__gte=start_date,
            publish_time__lte=end_date
        )

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        # 按日期和情感分组统计
        sentiment_timeline = {}
        for i in range(days + 1):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            sentiment_timeline[date_str] = {
                'positive': 0,
                'neutral': 0,
                'negative': 0
            }

        # 统计每日情感
        for post in queryset:
            date_str = post.publish_time.strftime('%Y-%m-%d')
            if date_str in sentiment_timeline:
                sentiment_timeline[date_str][post.sentiment] += 1

        # 构建时间线数据
        dates = sorted(sentiment_timeline.keys())
        positive_data = [sentiment_timeline[d]['positive'] for d in dates]
        neutral_data = [sentiment_timeline[d]['neutral'] for d in dates]
        negative_data = [sentiment_timeline[d]['negative'] for d in dates]

        data = {
            'dates': dates,
            'positive': positive_data,
            'neutral': neutral_data,
            'negative': negative_data
        }

        return Response(data)


class AnalysisLogViewSet(viewsets.ReadOnlyModelViewSet):
    """分析日志视图集"""
    queryset = AnalysisLog.objects.select_related('topic', 'created_by')
    serializer_class = AnalysisLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['topic', 'analysis_type', 'status']
    ordering = ['-created_at']
