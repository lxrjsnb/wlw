"""
话题和平台模型
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Platform(models.Model):
    """社交媒体平台（微博、微信、抖音等）"""

    PLATFORM_CHOICES = [
        ('weibo', '微博'),
        ('wechat', '微信'),
        ('douyin', '抖音'),
        ('zhihu', '知乎'),
        ('bilibili', 'B站'),
        ('xiaohongshu', '小红书'),
        ('toutiao', '今日头条'),
    ]

    name = models.CharField('平台名称', max_length=50)
    code = models.CharField('平台代码', max_length=20, unique=True, choices=PLATFORM_CHOICES)
    icon = models.CharField('图标', max_length=50, blank=True)
    color = models.CharField('主题色', max_length=20, default='#409EFF')
    is_active = models.BooleanField('是否启用', default=True)
    sort_order = models.IntegerField('排序', default=0)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'topics_platform'
        verbose_name = '社交媒体平台'
        verbose_name_plural = verbose_name
        ordering = ['sort_order', 'id']

    def __str__(self):
        return self.name


class Topic(models.Model):
    """监控话题"""

    STATUS_CHOICES = [
        ('active', '监控中'),
        ('paused', '已暂停'),
        ('archived', '已归档'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
    ]

    name = models.CharField('话题名称', max_length=200, db_index=True)
    description = models.TextField('描述', blank=True)
    keywords = models.JSONField('关键词列表', default=list, help_text='监控关键词列表')
    platforms = models.ManyToManyField(
        Platform,
        verbose_name='监控平台',
        related_name='topics',
        blank=True
    )
    status = models.CharField(
        '状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='负责人',
        related_name='topics'
    )
    priority = models.CharField(
        '优先级',
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'topics_topic'
        verbose_name = '监控话题'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority', 'status']),
        ]

    def __str__(self):
        return self.name

    @property
    def platform_count(self):
        return self.platforms.count()

    @property
    def post_count(self):
        from apps.posts.models import SocialPost
        return SocialPost.objects.filter(topic=self).count()
