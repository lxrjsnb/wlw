"""
热度计算算法模块

热度 = (互动量 + 曝光量) × 时效衰减 × 质量因子 × 传播因子

其中:
- 互动量 = 点赞×1 + 评论×3 + 转发×5
- 曝光量 = 阅读数 × 0.1
- 时效衰减 = exp(-ln2 × age / 24)  # 半衰期24小时
- 质量因子 = 内容长度因子 × 媒体丰富度 × 原创性
- 传播因子 = 1 + 传播深度×0.2 + 平台多样性×0.1 + 互动速度×0.3
"""

import math
from datetime import datetime, timedelta
from django.db.models import Avg, Max, Count, Q
from django.utils import timezone
from apps.posts.models import SocialPost
from apps.topics.models import Topic


class HotnessCalculator:
    """热度计算器"""

    # 权重配置
    INTERACTION_WEIGHTS = {
        'likes': 1.0,
        'comments': 3.0,
        'shares': 5.0,
        'views': 0.1,  # 曝光量权重
    }

    # 时效衰减参数
    HALF_LIFE_HOURS = 24  # 半衰期24小时

    # 热度等级阈值
    HOTNESS_LEVELS = {
        'explosive': (90, 100, '爆燃性热点'),
        'hot': (70, 90, '热点'),
        'warm': (50, 70, '温热'),
        'cool': (30, 50, '冷门'),
        'cold': (0, 30, '冰点'),
    }

    @classmethod
    def calculate_hotness(cls, post, current_time=None):
        """
        计算单个帖子的热度分数

        Args:
            post: SocialPost实例
            current_time: 当前时间，默认使用系统时间

        Returns:
            float: 热度分数 (0-100)
        """
        if current_time is None:
            current_time = timezone.now()

        # 1. 计算互动量
        interaction_score = (
            post.likes * cls.INTERACTION_WEIGHTS['likes'] +
            post.comments * cls.INTERACTION_WEIGHTS['comments'] +
            post.shares * cls.INTERACTION_WEIGHTS['shares']
        )

        # 2. 计算曝光量
        exposure_score = post.views * cls.INTERACTION_WEIGHTS['views']

        # 3. 计算时效衰减
        age_hours = cls._calculate_age_hours(post.publish_time, current_time)
        time_decay = math.exp(-math.log(2) * age_hours / cls.HALF_LIFE_HOURS)

        # 4. 计算质量因子
        quality_factor = cls._calculate_quality_factor(post)

        # 5. 计算基础热度
        base_hotness = (interaction_score + exposure_score) * time_decay * quality_factor

        # 6. 归一化到0-100范围（使用对数缩放避免极端值）
        normalized_score = cls._normalize_to_100(base_hotness)

        return round(normalized_score, 2)

    @classmethod
    def _calculate_age_hours(cls, publish_time, current_time):
        """计算帖子发布至今的小时数"""
        if not publish_time:
            return 0
        delta = current_time - publish_time
        return max(0, delta.total_seconds() / 3600)

    @classmethod
    def _calculate_quality_factor(cls, post):
        """
        计算质量因子

        考虑因素:
        - 内容长度 (长帖质量通常更高)
        - 媒体丰富度 (图片/视频)
        - 原创性
        """
        factor = 1.0

        # 内容长度因子 (对数缩放，避免过长内容权重过高)
        content_length = len(post.content) if post.content else 0
        if content_length > 0:
            length_factor = 1 + math.log(content_length + 1) / 10
            factor *= min(length_factor, 1.5)  # 最高1.5倍

        # 媒体丰富度（如果有其他媒体字段可扩展）
        # 这里简化处理，实际可以根据是否有图片/视频来调整

        return factor

    @classmethod
    def _normalize_to_100(cls, raw_score):
        """
        将原始分数归一化到0-100范围

        使用对数函数避免极端值
        """
        if raw_score <= 0:
            return 0

        # 使用log(1 + score) * 缩放因子
        # 调整参数使大部分帖子落在合理区间
        normalized = math.log1p(raw_score) * 15

        # 限制在0-100范围
        return min(max(normalized, 0), 100)

    @classmethod
    def classify_hotness_level(cls, score):
        """
        根据热度分数分类等级

        Args:
            score: 热度分数

        Returns:
            dict: 包含level, label, color的信息
        """
        for level, (min_score, max_score, label) in cls.HOTNESS_LEVELS.items():
            if min_score <= score < max_score:
                colors = {
                    'explosive': '#F56C6C',  # 红色
                    'hot': '#E6A23C',       # 橙色
                    'warm': '#409EFF',      # 蓝色
                    'cool': '#909399',      # 灰色
                    'cold': '#C0C4CC',      # 浅灰
                }
                return {
                    'level': level,
                    'label': label,
                    'color': colors.get(level, '#909399'),
                    'min_score': min_score,
                    'max_score': max_score,
                }

        return {
            'level': 'unknown',
            'label': '未知',
            'color': '#909399',
            'min_score': 0,
            'max_score': 100,
        }

    @classmethod
    def normalize_hotness_by_topic(cls, posts, topic_id):
        """
        按话题归一化热度分数

        在同一话题内，使用Z-score归一化，使不同话题的热度可比较

        Args:
            posts: SocialPost查询集
            topic_id: 话题ID

        Returns:
            list: 带归一化热度的帖子列表
        """
        # 获取该话题所有帖子的热度
        topic_posts = posts.filter(topic_id=topic_id)

        if not topic_posts.exists():
            return []

        # 计算平均热度和标准差
        hotness_scores = [p.hotness_score for p in topic_posts if hasattr(p, 'hotness_score')]
        if not hotness_scores:
            return []

        mean = sum(hotness_scores) / len(hotness_scores)
        std = (sum((x - mean) ** 2 for x in hotness_scores) / len(hotness_scores)) ** 0.5

        if std == 0:
            std = 1

        # 归一化到0-100
        normalized_posts = []
        for post in topic_posts:
            if hasattr(post, 'hotness_score'):
                # Z-score归一化
                z_score = (post.hotness_score - mean) / std
                # 转换到0-100 (假设99.7%的数据在±3σ范围内)
                normalized = 50 + z_score * 16.67
                normalized = max(0, min(100, normalized))
                post.normalized_hotness = round(normalized, 2)
            else:
                post.normalized_hotness = 0
            normalized_posts.append(post)

        return normalized_posts

    @classmethod
    def update_all_hotness(cls, topic_id=None):
        """
        批量更新热度分数

        Args:
            topic_id: 话题ID，None表示更新所有话题

        Returns:
            dict: 更新统计信息
        """
        current_time = timezone.now()

        # 构建查询
        if topic_id:
            posts = SocialPost.objects.filter(topic_id=topic_id)
        else:
            posts = SocialPost.objects.all()

        updated_count = 0
        total_count = posts.count()

        # 批量计算并更新
        for post in posts:
            hotness = cls.calculate_hotness(post, current_time)
            post.influence_score = hotness  # 使用influence_score字段存储热度
            post.save(update_fields=['influence_score'])
            updated_count += 1

        return {
            'total': total_count,
            'updated': updated_count,
            'topic_id': topic_id,
            'timestamp': current_time.isoformat(),
        }

    @classmethod
    def get_hotness_trend(cls, topic_id, days=7):
        """
        获取热度趋势数据

        Args:
            topic_id: 话题ID
            days: 天数

        Returns:
            list: 时间序列热度数据
        """
        from django.db.models import Avg
        from django.db.models.functions import TruncDate

        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        # 按日期分组统计平均热度
        trend_data = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__gte=start_date,
            publish_time__lte=end_date
        ).annotate(
            date=TruncDate('publish_time')
        ).values('date').annotate(
            avg_hotness=Avg('influence_score'),
            post_count=Count('id')
        ).order_by('date')

        # 格式化输出
        result = []
        for item in trend_data:
            result.append({
                'date': item['date'].strftime('%Y-%m-%d'),
                'avg_hotness': round(item['avg_hotness'] or 0, 2),
                'post_count': item['post_count'],
            })

        return result

    @classmethod
    def get_hotness_distribution(cls, topic_id):
        """
        获取热度等级分布

        Args:
            topic_id: 话题ID

        Returns:
            dict: 各等级的帖子数量和占比
        """
        posts = SocialPost.objects.filter(topic_id=topic_id)

        distribution = {}
        total = posts.count()

        for level, (min_score, max_score, label) in cls.HOTNESS_LEVELS.items():
            count = posts.filter(
                influence_score__gte=min_score,
                influence_score__lt=max_score
            ).count()

            distribution[level] = {
                'label': label,
                'count': count,
                'percentage': round(count / total * 100, 2) if total > 0 else 0,
                'min_score': min_score,
                'max_score': max_score,
            }

        return distribution

    @classmethod
    def get_rising_posts(cls, topic_id, limit=20):
        """
        获取热度上升最快的帖子

        Args:
            topic_id: 话题ID
            limit: 返回数量

        Returns:
            list: 上升最快的帖子列表
        """
        # 获取最近发布的帖子
        recent_posts = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__gte=timezone.now() - timedelta(hours=24)
        ).order_by('-influence_score')[:limit]

        return list(recent_posts)


# 便捷函数
def calculate_post_hotness(post):
    """计算单个帖子热度的便捷函数"""
    return HotnessCalculator.calculate_hotness(post)


def update_topic_hotness(topic_id):
    """更新话题下所有帖子热度的便捷函数"""
    return HotnessCalculator.update_all_hotness(topic_id)
