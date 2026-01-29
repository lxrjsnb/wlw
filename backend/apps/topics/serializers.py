"""
话题相关序列化器
"""
from rest_framework import serializers
from .models import Platform, Topic


class PlatformSerializer(serializers.ModelSerializer):
    """平台序列化器"""

    class Meta:
        model = Platform
        fields = ['id', 'name', 'code', 'icon', 'color', 'is_active', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class PlatformSimpleSerializer(serializers.ModelSerializer):
    """平台简单序列化器"""

    class Meta:
        model = Platform
        fields = ['id', 'name', 'code', 'icon', 'color']


class TopicSerializer(serializers.ModelSerializer):
    """话题序列化器"""

    owner_name = serializers.CharField(source='owner.username', read_only=True)
    platform_list = PlatformSimpleSerializer(
        source='platforms',
        many=True,
        read_only=True
    )
    platform_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    platform_count = serializers.ReadOnlyField()
    post_count = serializers.ReadOnlyField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'description', 'keywords', 'platform_list', 'platform_ids',
            'status', 'status_display', 'priority', 'priority_display',
            'owner', 'owner_name', 'platform_count', 'post_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        platform_ids = validated_data.pop('platform_ids', [])
        topic = Topic.objects.create(**validated_data)
        if platform_ids:
            topic.platforms.set(platform_ids)
        return topic

    def update(self, instance, validated_data):
        platform_ids = validated_data.pop('platform_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if platform_ids is not None:
            instance.platforms.set(platform_ids)
        return instance


class TopicListSerializer(serializers.ModelSerializer):
    """话题列表序列化器"""

    owner_name = serializers.CharField(source='owner.username', read_only=True)
    platform_names = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = Topic
        fields = [
            'id', 'name', 'description', 'keywords', 'platform_names',
            'status', 'status_display', 'priority', 'priority_display',
            'owner', 'owner_name', 'created_at'
        ]

    def get_platform_names(self, obj):
        return ', '.join([p.name for p in obj.platforms.all()])


class TopicStatsSerializer(serializers.Serializer):
    """话题统计序列化器"""
    total_topics = serializers.IntegerField()
    active_topics = serializers.IntegerField()
    paused_topics = serializers.IntegerField()
    archived_topics = serializers.IntegerField()
    high_priority_topics = serializers.IntegerField()
