"""
帖子相关序列化器
"""
from rest_framework import serializers
from .models import SocialPost, PostSummary
from apps.topics.serializers import TopicSerializer, PlatformSimpleSerializer


class SocialPostSerializer(serializers.ModelSerializer):
    """帖子序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    platform_color = serializers.CharField(source='platform.color', read_only=True)
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)
    total_engagement = serializers.ReadOnlyField()
    publish_time_formatted = serializers.DateTimeField(source='publish_time', format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = SocialPost
        fields = [
            'id', 'topic', 'topic_name', 'platform', 'platform_name', 'platform_color',
            'post_id', 'content', 'author', 'author_url', 'post_url',
            'publish_time', 'publish_time_formatted',
            'likes', 'comments', 'shares', 'views', 'total_engagement',
            'sentiment', 'sentiment_display', 'sentiment_score', 'keywords',
            'influence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'influence_score']


class SocialPostListSerializer(serializers.ModelSerializer):
    """帖子列表序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    platform_color = serializers.CharField(source='platform.color', read_only=True)
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)
    publish_time_formatted = serializers.DateTimeField(source='publish_time', format='%Y-%m-%d %H:%M', read_only=True)

    class Meta:
        model = SocialPost
        fields = [
            'id', 'post_id', 'topic_name', 'platform_name', 'platform_color',
            'content', 'author', 'sentiment', 'sentiment_display',
            'influence_score', 'publish_time', 'publish_time_formatted'
        ]


class SocialPostDetailSerializer(serializers.ModelSerializer):
    """帖子详情序列化器"""

    topic = TopicSerializer(read_only=True)
    platform = PlatformSimpleSerializer(read_only=True)
    sentiment_display = serializers.CharField(source='get_sentiment_display', read_only=True)
    total_engagement = serializers.ReadOnlyField()

    class Meta:
        model = SocialPost
        fields = '__all_model'


class PostSummarySerializer(serializers.ModelSerializer):
    """帖子汇总序列化器"""

    topic_name = serializers.CharField(source='topic.name', read_only=True)
    platform_name = serializers.CharField(source='platform.name', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    total_sentiment = serializers.ReadOnlyField()

    class Meta:
        model = PostSummary
        fields = [
            'id', 'topic', 'topic_name', 'platform', 'platform_name',
            'period', 'period_display', 'date', 'hour',
            'post_count', 'total_likes', 'total_comments', 'total_shares', 'total_views',
            'positive_count', 'neutral_count', 'negative_count', 'total_sentiment',
            'avg_sentiment_score', 'avg_influence_score', 'max_influence_score',
            'created_at', 'updated_at'
        ]


class PostStatsSerializer(serializers.Serializer):
    """帖子统计序列化器"""
    total_posts = serializers.IntegerField()
    today_posts = serializers.IntegerField()
    positive_count = serializers.IntegerField()
    neutral_count = serializers.IntegerField()
    negative_count = serializers.IntegerField()
    avg_sentiment_score = serializers.FloatField()
    avg_influence_score = serializers.FloatField()
    platform_distribution = serializers.ListField()
    sentiment_distribution = serializers.ListField()


class SentimentAnalysisRequestSerializer(serializers.Serializer):
    """情感分析请求序列化器"""
    text = serializers.CharField(required=True, max_length=10000)


class SentimentAnalysisResponseSerializer(serializers.Serializer):
    """情感分析响应序列化器"""
    sentiment = serializers.CharField()
    sentiment_score = serializers.FloatField()
    sentiment_label = serializers.CharField()
    keywords = serializers.ListField(child=serializers.CharField())
