"""
分析相关序列化器
"""
from rest_framework import serializers
from .models import AnalysisLog, KeywordTrend, InfluenceRanking, SentimentSnapshot


class AnalysisLogSerializer(serializers.ModelSerializer):
    """分析日志序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = AnalysisLog
        fields = [
            'id', 'topic', 'topic_name', 'analysis_type', 'analysis_type_display',
            'status', 'status_display', 'parameters', 'result', 'error_message',
            'started_at', 'completed_at', 'duration_seconds', 'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class KeywordTrendSerializer(serializers.ModelSerializer):
    """关键词趋势序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)

    class Meta:
        model = KeywordTrend
        fields = [
            'id', 'keyword', 'topic', 'topic_name', 'date', 'count',
            'sentiment_score', 'platforms', 'created_at'
        ]


class InfluenceRankingSerializer(serializers.ModelSerializer):
    """影响力排行序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)

    class Meta:
        model = InfluenceRanking
        fields = [
            'id', 'topic', 'topic_name', 'period', 'period_display',
            'date', 'top_posts', 'top_authors', 'top_keywords', 'created_at'
        ]


class SentimentSnapshotSerializer(serializers.ModelSerializer):
    """情感快照序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    positive_ratio = serializers.ReadOnlyField()
    negative_ratio = serializers.ReadOnlyField()

    class Meta:
        model = SentimentSnapshot
        fields = [
            'id', 'topic', 'topic_name', 'snapshot_time',
            'positive_count', 'neutral_count', 'negative_count', 'total_count',
            'positive_ratio', 'negative_ratio',
            'avg_sentiment_score', 'avg_influence_score', 'created_at'
        ]


class KeywordCloudSerializer(serializers.Serializer):
    """关键词云序列化器"""
    keywords = serializers.ListField(
        child=serializers.DictField()
    )


class TrendAnalysisSerializer(serializers.Serializer):
    """趋势分析序列化器"""
    dates = serializers.ListField()
    post_counts = serializers.ListField()
    sentiment_scores = serializers.ListField()
    influence_scores = serializers.ListField()


class PlatformCompareSerializer(serializers.Serializer):
    """平台对比序列化器"""
    platforms = serializers.ListField()
    post_counts = serializers.ListField()
    sentiment_scores = serializers.ListField()
    engagement_rates = serializers.ListField()
