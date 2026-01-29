"""
社交媒体帖子模型
"""
from django.db import models
from django.core.cache import cache
from django.db.models import Count, Avg, Sum, Q
from apps.topics.models import Topic, Platform


class SocialPostManager(models.Manager):
    """自定义帖子管理器"""

    def with_stats(self):
        """带统计数据的帖子查询集"""
        return self.get_queryset().select_related('topic', 'platform')

    def get_sentiment_stats(self, topic_id=None):
        """获取情感统计"""
        queryset = self.get_queryset()
        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        stats = queryset.aggregate(
            total=Count('id'),
            positive=Count('id', filter=Q(sentiment='positive')),
            neutral=Count('id', filter=Q(sentiment='neutral')),
            negative=Count('id', filter=Q(sentiment='negative')),
            avg_sentiment=Avg('sentiment_score'),
            avg_influence=Avg('influence_score')
        )
        return stats


class SocialPost(models.Model):
    """社交媒体帖子"""

    SENTIMENT_CHOICES = [
        ('positive', '正面'),
        ('neutral', '中性'),
        ('negative', '负面'),
    ]

    # 关联
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='posts',
        db_index=True
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.PROTECT,
        verbose_name='平台',
        related_name='posts'
    )

    # 帖子内容
    post_id = models.CharField('帖子ID', max_length=100, db_index=True)
    content = models.TextField('内容')
    author = models.CharField('作者', max_length=100)
    author_url = models.URLField('作者链接', blank=True)
    post_url = models.URLField('帖子链接', blank=True)

    # 数据指标
    publish_time = models.DateTimeField('发布时间', db_index=True)
    likes = models.IntegerField('点赞数', default=0)
    comments = models.IntegerField('评论数', default=0)
    shares = models.IntegerField('转发数', default=0)
    views = models.IntegerField('阅读数', default=0)

    # 情感分析
    sentiment = models.CharField(
        '情感倾向',
        max_length=20,
        choices=SENTIMENT_CHOICES,
        default='neutral',
        db_index=True
    )
    sentiment_score = models.FloatField('情感分数', null=True, help_text='-1到1之间，负数为负面，正数为正面')
    keywords = models.JSONField('关键词', null=True, blank=True, help_text='提取的关键词列表')

    # 影响力
    influence_score = models.FloatField('影响力分数', default=0, db_index=True, help_text='综合影响力评分')

    # 元数据
    created_at = models.DateTimeField('采集时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    objects = SocialPostManager()

    class Meta:
        db_table = 'posts_social_post'
        verbose_name = '社交媒体帖子'
        verbose_name_plural = verbose_name
        ordering = ['-publish_time']
        indexes = [
            models.Index(fields=['topic', '-publish_time']),
            models.Index(fields=['sentiment', '-publish_time']),
            models.Index(fields=['-influence_score']),
            models.Index(fields=['platform', '-publish_time']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['platform', 'post_id'],
                name='unique_platform_post'
            )
        ]

    def __str__(self):
        return f"{self.platform.name} - {self.author}: {self.content[:50]}"

    def save(self, *args, **kwargs):
        # 自动计算影响力分数
        if not self.influence_score:
            self.calculate_influence()
        super().save(*args, **kwargs)

    def calculate_influence(self):
        """计算影响力分数"""
        # 综合点赞、评论、转发和阅读数计算影响力
        self.influence_score = (
            self.likes * 0.3 +
            self.comments * 0.5 +
            self.shares * 0.8 +
            self.views * 0.01
        )

    @property
    def total_engagement(self):
        """总互动数"""
        return self.likes + self.comments + self.shares

    @property
    def sentiment_label(self):
        """情感标签"""
        return dict(self.SENTIMENT_CHOICES).get(self.sentiment, '未知')


class PostSummary(models.Model):
    """帖子汇总（按时间维度汇总统计数据）"""

    PERIOD_CHOICES = [
        ('hourly', '每小时'),
        ('daily', '每日'),
        ('weekly', '每周'),
        ('monthly', '每月'),
    ]

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='summaries',
        db_index=True
    )
    platform = models.ForeignKey(
        Platform,
        on_delete=models.PROTECT,
        verbose_name='平台',
        related_name='summaries',
        null=True,
        blank=True
    )

    period = models.CharField('统计周期', max_length=20, choices=PERIOD_CHOICES)
    date = models.DateField('日期', db_index=True)
    hour = models.IntegerField('小时', null=True, blank=True)

    # 统计数据
    post_count = models.IntegerField('帖子数', default=0)
    total_likes = models.IntegerField('总点赞数', default=0)
    total_comments = models.IntegerField('总评论数', default=0)
    total_shares = models.IntegerField('总转发数', default=0)
    total_views = models.IntegerField('总阅读数', default=0)

    # 情感统计
    positive_count = models.IntegerField('正面数', default=0)
    neutral_count = models.IntegerField('中性数', default=0)
    negative_count = models.IntegerField('负面数', default=0)
    avg_sentiment_score = models.FloatField('平均情感分', default=0)

    # 影响力
    avg_influence_score = models.FloatField('平均影响力', default=0)
    max_influence_score = models.FloatField('最高影响力', default=0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'posts_summary'
        verbose_name = '帖子汇总'
        verbose_name_plural = verbose_name
        ordering = ['-date', '-hour']
        indexes = [
            models.Index(fields=['topic', '-date']),
            models.Index(fields=['topic', 'period', '-date']),
            models.Index(fields=['platform', '-date']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['topic', 'platform', 'period', 'date', 'hour'],
                name='unique_summary_period',
                condition=Q(platform__isnull=False)
            )
        ]

    def __str__(self):
        platform_name = self.platform.name if self.platform else '全部平台'
        return f"{self.topic.name} - {platform_name} - {self.date}"

    @property
    def total_sentiment(self):
        """总情感相关帖子数"""
        return self.positive_count + self.neutral_count + self.negative_count
