"""
分析服务和日志模型
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.topics.models import Topic

User = get_user_model()


class AnalysisLog(models.Model):
    """分析日志"""

    ANALYSIS_TYPE_CHOICES = [
        ('sentiment', '情感分析'),
        ('keyword', '关键词提取'),
        ('trend', '趋势分析'),
        ('influence', '影响力分析'),
        ('custom', '自定义分析'),
    ]

    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='analysis_logs',
        null=True,
        blank=True
    )
    analysis_type = models.CharField(
        '分析类型',
        max_length=20,
        choices=ANALYSIS_TYPE_CHOICES,
        db_index=True
    )
    status = models.CharField(
        '状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    parameters = models.JSONField('分析参数', null=True, blank=True)
    result = models.JSONField('分析结果', null=True, blank=True)
    error_message = models.TextField('错误信息', blank=True)
    started_at = models.DateTimeField('开始时间', null=True, blank=True)
    completed_at = models.DateTimeField('完成时间', null=True, blank=True)
    duration_seconds = models.FloatField('耗时(秒)', null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='创建人',
        related_name='analysis_logs'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'analysis_log'
        verbose_name = '分析日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['topic', '-created_at']),
            models.Index(fields=['analysis_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        topic_name = self.topic.name if self.topic else '全局分析'
        return f"{topic_name} - {self.get_analysis_type_display()} ({self.get_status_display()})"


class KeywordTrend(models.Model):
    """关键词趋势"""

    keyword = models.CharField('关键词', max_length=100, db_index=True)
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='keyword_trends',
        db_index=True
    )
    date = models.DateField('日期', db_index=True)
    count = models.IntegerField('出现次数', default=0)
    sentiment_score = models.FloatField('情感分数', default=0)
    platforms = models.JSONField('平台分布', null=True, blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'analysis_keyword_trend'
        verbose_name = '关键词趋势'
        verbose_name_plural = verbose_name
        ordering = ['-date', '-count']
        indexes = [
            models.Index(fields=['topic', '-date']),
            models.Index(fields=['keyword', '-date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['topic', 'keyword', 'date'],
                name='unique_keyword_date'
            )
        ]

    def __str__(self):
        return f"{self.keyword} - {self.date} ({self.count})"


class InfluenceRanking(models.Model):
    """影响力排行（缓存表）"""

    PERIOD_CHOICES = [
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
    ]

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='influence_rankings',
        db_index=True
    )
    period = models.CharField('统计周期', max_length=20, choices=PERIOD_CHOICES)
    date = models.DateField('日期', db_index=True)

    # 排行数据（JSON存储前N名）
    top_posts = models.JSONField('热门帖子', default=list)
    top_authors = models.JSONField('热门作者', default=list)
    top_keywords = models.JSONField('热门关键词', default=list)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'analysis_influence_ranking'
        verbose_name = '影响力排行'
        verbose_name_plural = verbose_name
        ordering = ['-date']
        indexes = [
            models.Index(fields=['topic', 'period', '-date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['topic', 'period', 'date'],
                name='unique_ranking_period'
            )
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.get_period_display()} - {self.date}"


class SentimentSnapshot(models.Model):
    """情感快照（时间点情感分布）"""

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='sentiment_snapshots',
        db_index=True
    )
    snapshot_time = models.DateTimeField('快照时间', db_index=True)

    # 情感分布
    positive_count = models.IntegerField('正面数', default=0)
    neutral_count = models.IntegerField('中性数', default=0)
    negative_count = models.IntegerField('负面数', default=0)
    total_count = models.IntegerField('总数', default=0)

    # 平均分数
    avg_sentiment_score = models.FloatField('平均情感分', default=0)
    avg_influence_score = models.FloatField('平均影响力', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'analysis_sentiment_snapshot'
        verbose_name = '情感快照'
        verbose_name_plural = verbose_name
        ordering = ['-snapshot_time']
        indexes = [
            models.Index(fields=['topic', '-snapshot_time']),
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.snapshot_time}"

    @property
    def positive_ratio(self):
        """正面比例"""
        if self.total_count == 0:
            return 0
        return round(self.positive_count / self.total_count * 100, 2)

    @property
    def negative_ratio(self):
        """负面比例"""
        if self.total_count == 0:
            return 0
        return round(self.negative_count / self.total_count * 100, 2)
