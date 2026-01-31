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


# ============== 新增ViewSet: 深度分析功能 ==============


class HotnessViewSet(viewsets.GenericViewSet):
    """热度分析视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def realtime(self, request):
        """实时热度排行榜"""
        from .hotness_calculator import HotnessCalculator

        topic_id = request.query_params.get('topic')
        limit = int(request.query_params.get('limit', 20))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 先更新热度分数
        HotnessCalculator.update_all_hotness(topic_id)

        # 获取排行榜
        posts = SocialPost.objects.filter(topic_id=topic_id).order_by('-influence_score')[:limit]

        data = []
        for post in posts:
            hotness = post.influence_score
            level_info = HotnessCalculator.classify_hotness_level(hotness)
            data.append({
                'post_id': post.id,
                'content': post.content[:100],
                'author': post.author,
                'platform': post.platform.name,
                'hotness': round(hotness, 2),
                'level': level_info['level'],
                'level_label': level_info['label'],
                'color': level_info['color'],
                'likes': post.likes,
                'comments': post.comments,
                'shares': post.shares,
                'publish_time': post.publish_time.isoformat() if post.publish_time else None,
            })

        return Response({'ranking': data})

    @action(detail=False, methods=['get'])
    def trend(self, request):
        """热度趋势"""
        from .hotness_calculator import HotnessCalculator

        topic_id = request.query_params.get('topic')
        days = int(request.query_params.get('days', 7))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        trend_data = HotnessCalculator.get_hotness_trend(topic_id, days)

        return Response({'trend': trend_data, 'period_days': days})

    @action(detail=False, methods=['get'])
    def distribution(self, request):
        """热度等级分布"""
        from .hotness_calculator import HotnessCalculator

        topic_id = request.query_params.get('topic')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        distribution = HotnessCalculator.get_hotness_distribution(topic_id)

        return Response({'distribution': distribution})

    @action(detail=False, methods=['get'])
    def rising(self, request):
        """热度上升最快"""
        from .hotness_calculator import HotnessCalculator

        topic_id = request.query_params.get('topic')
        limit = int(request.query_params.get('limit', 20))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        posts = HotnessCalculator.get_rising_posts(topic_id, limit)

        data = []
        for post in posts:
            data.append({
                'post_id': post.id,
                'content': post.content[:100],
                'author': post.author,
                'hotness': round(post.influence_score, 2),
                'publish_time': post.publish_time.isoformat() if post.publish_time else None,
            })

        return Response({'rising_posts': data})


class PropagationViewSet(viewsets.GenericViewSet):
    """传播分析视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def paths(self, request):
        """传播路径列表"""
        from .propagation_analyzer import PropagationAnalyzer

        topic_id = request.query_params.get('topic')
        limit = int(request.query_params.get('limit', 10))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取最近的传播分析
        from .models import PropagationPath
        paths = PropagationPath.objects.filter(
            post__topic_id=topic_id
        ).order_by('-created_at')[:limit]

        data = []
        for path in paths:
            data.append({
                'id': path.id,
                'post_id': path.post_id,
                'pattern': path.pattern,
                'pattern_label': path.get_pattern_display(),
                'depth': path.depth,
                'breadth': path.breadth,
                'speed': path.speed,
                'key_nodes': path.key_nodes[:5],
                'created_at': path.created_at.isoformat(),
            })

        return Response({'paths': data})

    @action(detail=False, methods=['get'])
    def key_nodes(self, request):
        """关键节点Top排行"""
        from .propagation_analyzer import PropagationAnalyzer

        topic_id = request.query_params.get('topic')
        limit = int(request.query_params.get('limit', 10))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 构建传播图
        posts = SocialPost.objects.filter(topic_id=topic_id)
        graph = PropagationAnalyzer.build_propagation_graph(posts)

        # 识别关键节点
        key_nodes = PropagationAnalyzer.identify_key_nodes(graph, top_k=limit)

        return Response({'key_nodes': key_nodes})

    @action(detail=False, methods=['get'])
    def pattern(self, request):
        """传播模式识别"""
        from .propagation_analyzer import PropagationAnalyzer
        from .models import PropagationPath

        topic_id = request.query_params.get('topic')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 获取最近的传播模式统计
        paths = PropagationPath.objects.filter(post__topic_id=topic_id)

        pattern_dist = {}
        for path in paths:
            pattern = path.pattern
            if pattern not in pattern_dist:
                pattern_dist[pattern] = {
                    'pattern': pattern,
                    'label': path.get_pattern_display(),
                    'count': 0,
                }
            pattern_dist[pattern]['count'] += 1

        # 获取统计概览
        stats = PropagationAnalyzer.get_propagation_stats(topic_id)

        return Response({
            'pattern_distribution': list(pattern_dist.values()),
            'statistics': stats,
        })

    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """分析帖子传播"""
        from .propagation_analyzer import PropagationAnalyzer

        post_id = request.data.get('post_id')

        if not post_id:
            return Response({'error': '请提供post_id参数'}, status=status.HTTP_400_BAD_REQUEST)

        result = PropagationAnalyzer.analyze_propagation(post_id)

        if result:
            return Response({
                'id': result.id,
                'pattern': result.pattern,
                'depth': result.depth,
                'breadth': result.breadth,
                'key_nodes': result.key_nodes,
            })
        else:
            return Response({'error': '帖子不存在或分析失败'}, status=status.HTTP_404_NOT_FOUND)


class EmergencyViewSet(viewsets.GenericViewSet):
    """突发事件视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def detect(self, request):
        """检测突发事件"""
        from .emergency_detector import EmergencyDetector

        topic_id = request.query_params.get('topic')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 执行检测
        events = EmergencyDetector.detect_emergency_event(topic_id)

        return Response({
            'detected_events': events,
            'count': len(events),
            'timestamp': timezone.now().isoformat(),
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """活跃突发事件列表"""
        from .emergency_detector import EmergencyDetector

        topic_id = request.query_params.get('topic')

        events = EmergencyDetector.get_active_emergencies(topic_id)

        data = []
        for event in events:
            data.append({
                'id': event.id,
                'topic': event.topic.name,
                'event_type': event.event_type,
                'event_type_label': event.get_event_type_display(),
                'severity': event.severity,
                'severity_label': event.get_severity_display(),
                'status': event.status,
                'detected_at': event.detected_at.isoformat(),
                'metrics': event.metrics,
            })

        return Response({'active_emergencies': data})

    @action(detail=False, methods=['get'])
    def history(self, request):
        """历史事件"""
        from .models import EmergencyEvent

        topic_id = request.query_params.get('topic')
        limit = int(request.query_params.get('limit', 50))

        queryset = EmergencyEvent.objects.all()

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        events = queryset.order_by('-detected_at')[:limit]

        data = []
        for event in events:
            data.append({
                'id': event.id,
                'topic': event.topic.name,
                'event_type': event.event_type,
                'event_type_label': event.get_event_type_display(),
                'severity': event.severity,
                'severity_label': event.get_severity_display(),
                'status': event.status,
                'detected_at': event.detected_at.isoformat(),
                'resolved_at': event.resolved_at.isoformat() if event.resolved_at else None,
            })

        return Response({'history': data})

    @action(detail=False, methods=['post'])
    def resolve(self, request):
        """解决事件"""
        from .emergency_detector import EmergencyDetector

        event_id = request.data.get('event_id')
        notes = request.data.get('notes', '')

        if not event_id:
            return Response({'error': '请提供event_id参数'}, status=status.HTTP_400_BAD_REQUEST)

        success = EmergencyDetector.resolve_emergency(
            event_id,
            request.user.id,
            notes
        )

        if success:
            return Response({'message': '事件已标记为解决'})
        else:
            return Response({'error': '事件不存在'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def mark_false_positive(self, request):
        """标记误报"""
        from .emergency_detector import EmergencyDetector

        event_id = request.data.get('event_id')
        notes = request.data.get('notes', '')

        if not event_id:
            return Response({'error': '请提供event_id参数'}, status=status.HTTP_400_BAD_REQUEST)

        success = EmergencyDetector.mark_false_positive(
            event_id,
            request.user.id,
            notes
        )

        if success:
            return Response({'message': '事件已标记为误报'})
        else:
            return Response({'error': '事件不存在'}, status=status.HTTP_404_NOT_FOUND)


class KOLViewSet(viewsets.GenericViewSet):
    """KOL分析视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def ranking(self, request):
        """KOL排行榜"""
        from .kol_detector import KOLDetector

        topic_id = request.query_params.get('topic')
        limit = int(request.query_params.get('limit', 20))
        sort_by = request.query_params.get('sort_by', 'kol_score')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        # 先更新KOL数据
        KOLDetector.update_kol_rankings(topic_id)

        # 获取排行榜
        kols = KOLDetector.get_top_kols(topic_id, limit, sort_by)

        data = []
        for kol in kols:
            data.append({
                'author': kol.author,
                'kol_score': round(kol.kol_score, 2),
                'kol_type': kol.kol_type,
                'kol_type_label': kol.get_kol_type_display(),
                'content_influence': round(kol.content_influence, 4),
                'network_influence': round(kol.network_influence, 4),
                'topic_leadership': round(kol.topic_leadership, 4),
                'sentiment_influence': round(kol.sentiment_influence, 4),
                'post_count': kol.post_count,
                'total_likes': kol.total_likes,
                'total_comments': kol.total_comments,
            })

        return Response({'ranking': data, 'sort_by': sort_by})

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """KOL画像详情"""
        from .kol_detector import KOLDetector

        topic_id = request.query_params.get('topic')
        author = request.query_params.get('author')

        if not topic_id or not author:
            return Response({'error': '请提供topic和author参数'}, status=status.HTTP_400_BAD_REQUEST)

        profile = KOLDetector.get_kol_profile(topic_id, author)

        if not profile:
            return Response({'error': 'KOL画像不存在'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'author': profile.author,
            'kol_type': profile.kol_type,
            'kol_type_label': profile.get_kol_type_display(),
            'kol_score': round(profile.kol_score, 2),
            'dimensions': {
                'content': round(profile.content_influence, 4),
                'network': round(profile.network_influence, 4),
                'leadership': round(profile.topic_leadership, 4),
                'sentiment': round(profile.sentiment_influence, 4),
            },
            'statistics': {
                'post_count': profile.post_count,
                'total_likes': profile.total_likes,
                'total_comments': profile.total_comments,
                'total_shares': profile.total_shares,
                'avg_sentiment': round(profile.avg_sentiment_score, 3),
            },
            'centrality': {
                'pagerank': round(profile.pagerank_score, 4),
                'betweenness': round(profile.betweenness_centrality, 4),
                'closeness': round(profile.closeness_centrality, 4),
            },
        })

    @action(detail=False, methods=['get'])
    def classify(self, request):
        """KOL分类分布"""
        from .kol_detector import KOLDetector

        topic_id = request.query_params.get('topic')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        distribution = KOLDetector.get_kol_type_distribution(topic_id)

        return Response({'distribution': distribution})


class EvolutionViewSet(viewsets.GenericViewSet):
    """舆情演化视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def current_stage(self, request):
        """当前演化阶段"""
        from .evolution_tracker import OpinionEvolutionTracker

        topic_id = request.query_params.get('topic')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        stage_info = OpinionEvolutionTracker.classify_evolution_stage(topic_id)

        if not stage_info:
            return Response({'error': '话题不存在或无数据'}, status=status.HTTP_404_NOT_FOUND)

        # 获取预测
        prediction = OpinionEvolutionTracker.predict_next_stage(topic_id)

        return Response({
            'current_stage': stage_info.get('stage'),
            'stage_label': stage_info.get('stage_label'),
            'description': stage_info.get('description'),
            'metrics': stage_info.get('metrics', {}),
            'prediction': prediction,
        })

    @action(detail=False, methods=['get'])
    def history(self, request):
        """演化历史"""
        from .evolution_tracker import OpinionEvolutionTracker

        topic_id = request.query_params.get('topic')
        limit = int(request.query_params.get('limit', 50))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        history = OpinionEvolutionTracker.get_evolution_history(topic_id, limit)

        return Response({'history': history})

    @action(detail=False, methods=['get'])
    def predict(self, request):
        """阶段预测"""
        from .evolution_tracker import OpinionEvolutionTracker

        topic_id = request.query_params.get('topic')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        prediction = OpinionEvolutionTracker.predict_next_stage(topic_id)

        return Response({'prediction': prediction})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """阶段统计"""
        from .evolution_tracker import OpinionEvolutionTracker

        topic_id = request.query_params.get('topic')

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        stats = OpinionEvolutionTracker.get_stage_statistics(topic_id)

        return Response({'stage_statistics': stats})


class SentimentAnalysisViewSet(viewsets.GenericViewSet):
    """情感分析视图集"""
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def multilevel(self, request):
        """多层次情感分析"""
        from .sentiment_analyzer import SentimentAnalyzer

        topic_id = request.query_params.get('topic')
        days = int(request.query_params.get('days', 7))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        stats = SentimentAnalyzer.get_multilevel_sentiment_stats(topic_id, days)

        return Response(stats)

    @action(detail=False, methods=['get'])
    def intensity(self, request):
        """情感强度分析"""
        from .sentiment_analyzer import SentimentAnalyzer

        text = request.query_params.get('text')

        if not text:
            return Response({'error': '请提供text参数'}, status=status.HTTP_400_BAD_REQUEST)

        intensity = SentimentAnalyzer.calculate_sentiment_intensity(text)
        analysis = SentimentAnalyzer.analyze_sentiment_multilevel(text)

        return Response({
            'intensity': round(intensity, 3),
            'analysis': analysis,
        })

    @action(detail=False, methods=['get'])
    def evolution(self, request):
        """情感演化追踪"""
        from .sentiment_analyzer import SentimentAnalyzer

        topic_id = request.query_params.get('topic')
        user_id = request.query_params.get('user')
        days = int(request.query_params.get('days', 7))

        if not topic_id:
            return Response({'error': '请提供topic参数'}, status=status.HTTP_400_BAD_REQUEST)

        if user_id:
            # 追踪特定用户的情感演化
            evolution = SentimentAnalyzer.track_sentiment_evolution(user_id, topic_id, days)
        else:
            # 返回整体情感统计
            evolution = SentimentAnalyzer.get_multilevel_sentiment_stats(topic_id, days)

        return Response({'evolution': evolution})
