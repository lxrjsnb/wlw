from django.contrib import admin
from .models import AnalysisLog, KeywordTrend, InfluenceRanking, SentimentSnapshot


@admin.register(AnalysisLog)
class AnalysisLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'analysis_type', 'status', 'duration_seconds', 'created_by', 'created_at']
    list_filter = ['analysis_type', 'status', 'topic']
    search_fields = ['error_message']
    readonly_fields = ['created_at', 'started_at', 'completed_at']


@admin.register(KeywordTrend)
class KeywordTrendAdmin(admin.ModelAdmin):
    list_display = ['keyword', 'topic', 'date', 'count', 'sentiment_score']
    list_filter = ['topic', 'date']
    search_fields = ['keyword']
    date_hierarchy = 'date'


@admin.register(InfluenceRanking)
class InfluenceRankingAdmin(admin.ModelAdmin):
    list_display = ['topic', 'period', 'date', 'created_at']
    list_filter = ['period', 'topic']
    date_hierarchy = 'date'


@admin.register(SentimentSnapshot)
class SentimentSnapshotAdmin(admin.ModelAdmin):
    list_display = ['topic', 'snapshot_time', 'total_count', 'positive_ratio', 'negative_ratio', 'avg_sentiment_score']
    list_filter = ['topic']
    date_hierarchy = 'snapshot_time'

    def positive_ratio(self, obj):
        return f"{obj.positive_ratio}%"
    positive_ratio.short_description = '正面比例'

    def negative_ratio(self, obj):
        return f"{obj.negative_ratio}%"
    negative_ratio.short_description = '负面比例'
