from django.contrib import admin
from .models import SocialPost, PostSummary


@admin.register(SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'platform', 'author', 'sentiment', 'influence_score', 'publish_time', 'created_at']
    list_filter = ['sentiment', 'platform', 'topic']
    search_fields = ['content', 'author', 'post_id']
    readonly_fields = ['created_at', 'updated_at', 'influence_score']
    date_hierarchy = 'publish_time'


@admin.register(PostSummary)
class PostSummaryAdmin(admin.ModelAdmin):
    list_display = ['topic', 'platform', 'period', 'date', 'hour', 'post_count', 'avg_sentiment_score']
    list_filter = ['period', 'topic', 'platform']
    date_hierarchy = 'date'
