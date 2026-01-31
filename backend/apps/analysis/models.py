"""
分析服务和日志模型
"""
from django.db import models
from django.contrib.auth import get_user_model
from apps.topics.models import Topic

User = get_user_model()


# ============== 新增模型：深度分析功能 ==============


class PropagationPath(models.Model):
    """传播路径分析"""

    PATTERN_CHOICES = [
        ('star', '星型传播'),
        ('chain', '链式传播'),
        ('viral', '病毒式传播'),
        ('community', '社区传播'),
        ('unknown', '未知'),
    ]

    # 关联帖子
    post = models.ForeignKey(
        'posts.SocialPost',
        on_delete=models.CASCADE,
        verbose_name='原始帖子',
        related_name='propagation_paths',
        db_index=True
    )

    # 传播路径数据（JSON格式存储节点和边）
    path_data = models.JSONField(
        '传播路径数据',
        default=dict,
        help_text='存储传播图的结构，包含节点和边'
    )

    # 传播指标
    depth = models.IntegerField('传播深度', default=0, help_text='传播层级数')
    breadth = models.IntegerField('传播广度', default=0, help_text='覆盖节点数')
    speed = models.FloatField('传播速度', default=0, help_text='每小时新增节点数')

    # 传播模式
    pattern = models.CharField(
        '传播模式',
        max_length=50,
        choices=PATTERN_CHOICES,
        default='unknown'
    )

    # 关键节点（Top K 影响力节点）
    key_nodes = models.JSONField('关键节点', default=list, help_text='传播中关键的节点列表')

    # 统计信息
    total_nodes = models.IntegerField('总节点数', default=0)
    total_edges = models.IntegerField('总边数', default=0)

    created_at = models.DateTimeField('分析时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'analysis_propagation_path'
        verbose_name = '传播路径'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['pattern', '-created_at']),
        ]

    def __str__(self):
        return f"{self.post_id} - {self.get_pattern_display()} (深度:{self.depth})"


class KOLProfile(models.Model):
    """KOL（关键意见领袖）画像"""

    KOL_TYPE_CHOICES = [
        ('initiator', '发起者'),
        ('spreader', '传播者'),
        ('guide', '引导者'),
        ('comprehensive', '综合影响力者'),
    ]

    # 用户标识
    author = models.CharField('作者', max_length=100, db_index=True)
    author_url = models.URLField('作者链接', blank=True)

    # 关联话题
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='kol_profiles',
        db_index=True
    )

    # KOL类型
    kol_type = models.CharField(
        'KOL类型',
        max_length=50,
        choices=KOL_TYPE_CHOICES,
        default='comprehensive'
    )

    # 综合得分
    kol_score = models.FloatField('KOL综合得分', default=0, db_index=True)

    # 四维影响力评分
    content_influence = models.FloatField('内容影响力', default=0, help_text='权重40%')
    network_influence = models.FloatField('网络影响力', default=0, help_text='权重30%')
    topic_leadership = models.FloatField('话题引领力', default=0, help_text='权重20%')
    sentiment_influence = models.FloatField('情感影响力', default=0, help_text='权重10%')

    # 统计数据
    post_count = models.IntegerField('帖子数', default=0)
    total_likes = models.IntegerField('总点赞数', default=0)
    total_comments = models.IntegerField('总评论数', default=0)
    total_shares = models.IntegerField('总转发数', default=0)
    avg_sentiment_score = models.FloatField('平均情感分', default=0)

    # PageRank等中心性指标
    pagerank_score = models.FloatField('PageRank得分', default=0)
    betweenness_centrality = models.FloatField('介数中心性', default=0)
    closeness_centrality = models.FloatField('接近中心性', default=0)

    # 元数据
    followers_count = models.IntegerField('粉丝数', default=0, null=True)
    is_verified = models.BooleanField('是否认证', default=False)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'analysis_kol_profile'
        verbose_name = 'KOL画像'
        verbose_name_plural = verbose_name
        ordering = ['-kol_score']
        indexes = [
            models.Index(fields=['topic', '-kol_score']),
            models.Index(fields=['author', 'topic']),
            models.Index(fields=['kol_type', '-kol_score']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'topic'],
                name='unique_author_topic_kol'
            )
        ]

    def __str__(self):
        return f"{self.author} - {self.get_kol_type_display()} ({self.kol_score:.2f})"


class EmergencyEvent(models.Model):
    """突发事件检测"""

    EVENT_TYPE_CHOICES = [
        ('volume_spike', '数量突发'),
        ('sentiment_shift', '情感突变'),
        ('hotness_surge', '热度激增'),
        ('combined', '综合异常'),
    ]

    SEVERITY_CHOICES = [
        ('level1', 'Level 1 - 紧急'),
        ('level2', 'Level 2 - 重要'),
        ('level3', 'Level 3 - 一般'),
    ]

    STATUS_CHOICES = [
        ('active', '活跃'),
        ('resolved', '已解决'),
        ('false_positive', '误报'),
    ]

    # 关联话题
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='emergency_events',
        db_index=True
    )

    # 检测信息
    detected_at = models.DateTimeField('检测时间', auto_now_add=True, db_index=True)
    event_type = models.CharField('事件类型', max_length=50, choices=EVENT_TYPE_CHOICES)
    severity = models.CharField('严重程度', max_length=50, choices=SEVERITY_CHOICES, default='level3')

    # 异常指标（JSON存储各种异常数据）
    metrics = models.JSONField('异常指标', default=dict, help_text='存储检测到异常的各项指标')

    # 状态管理
    status = models.CharField('状态', max_length=50, choices=STATUS_CHOICES, default='active')
    alert_triggered = models.BooleanField('是否触发预警', default=False)

    # 处理信息
    resolved_at = models.DateTimeField('解决时间', null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='处理人',
        related_name='resolved_emergencies'
    )
    notes = models.TextField('处理备注', blank=True)

    # 元数据
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'analysis_emergency_event'
        verbose_name = '突发事件'
        verbose_name_plural = verbose_name
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['topic', '-detected_at']),
            models.Index(fields=['status', '-detected_at']),
            models.Index(fields=['severity', '-detected_at']),
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.get_event_type_display()} ({self.get_severity_display()})"


class OpinionEvolution(models.Model):
    """舆情演化阶段追踪"""

    STAGE_CHOICES = [
        ('latent', '潜伏期'),
        ('germination', '萌发期'),
        ('explosion', '爆发期'),
        ('diffusion', '扩散期'),
        ('decline', '衰退期'),
        ('death', '消亡期'),
    ]

    # 关联话题
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        verbose_name='话题',
        related_name='evolution_stages',
        db_index=True
    )

    # 阶段信息
    stage = models.CharField('演化阶段', max_length=50, choices=STAGE_CHOICES, db_index=True)
    started_at = models.DateTimeField('阶段开始时间', auto_now_add=True)
    ended_at = models.DateTimeField('阶段结束时间', null=True, blank=True)
    duration_hours = models.FloatField('持续时长(小时)', null=True, blank=True)

    # 阶段指标
    peak_hotness = models.FloatField('峰值热度', default=0)
    post_count = models.IntegerField('帖子数', default=0)
    avg_sentiment = models.FloatField('平均情感', default=0)

    # 转换指标（记录从上一阶段到该阶段的变化）
    transition_metrics = models.JSONField('转换指标', default=dict, help_text='阶段转换时的关键指标变化')

    # 预测信息
    predicted_next_stage = models.CharField('预测下一阶段', max_length=50, blank=True)
    predicted_duration = models.FloatField('预测持续时长(小时)', null=True, blank=True)
    confidence = models.FloatField('预测置信度', default=0, help_text='0-1之间')

    # 基线数据（用于异常检测）
    baseline_metrics = models.JSONField('基线指标', default=dict, help_text='该阶段的历史基线数据')

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'analysis_opinion_evolution'
        verbose_name = '舆情演化'
        verbose_name_plural = verbose_name
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['topic', '-started_at']),
            models.Index(fields=['stage', '-started_at']),
        ]

    def __str__(self):
        return f"{self.topic.name} - {self.get_stage_display()} ({self.started_at})"


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
