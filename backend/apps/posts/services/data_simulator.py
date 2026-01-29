"""
社交媒体数据模拟器
"""
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.utils import timezone

from apps.posts.models import SocialPost
from apps.topics.models import Topic, Platform
from .sentiment_analyzer import SentimentAnalyzer


class SocialDataSimulator:
    """社交媒体数据模拟器"""

    # 模拟内容模板
    SAMPLE_CONTENTS = {
        'positive': [
            "这个话题真的很有意义！完全支持",
            "我觉得这个观点非常有道理，强烈推荐",
            "非常好！这正是我们需要的",
            "太棒了，终于有人关注这个问题了",
            "非常有建设性的意见，值得深思",
            "完全同意这个看法！做得好",
            "这个质量真的很高，必须点赞",
            "说得对！就是这样，支持到底",
            "真的很不错，值得大家关注",
            "这才是真正有价值的内容",
        ],
        'neutral': [
            "我觉得还需要再观察一下",
            "这个观点有待商榷，可以讨论",
            "整体来看还不错，但有些地方可以改进",
            "从我的角度来看，这需要综合考虑",
            "还需要更多的数据和证据来支持",
            "这个问题比较复杂，需要深入研究",
            "目前还不能下结论，拭目以待吧",
            "有些道理，但也不全对",
            "可以作为一个参考，但不绝对",
            "需要从多个角度来看这个问题",
        ],
        'negative': [
            "不太同意这种看法，有失偏颇",
            "我觉得这个方案还有很多问题",
            "完全不理解为什么会这样",
            "这简直是在浪费时间",
            "非常失望，完全不是预期的结果",
            "这个做法不对，应该重新考虑",
            "有很多明显的漏洞，无法接受",
            "太糟糕了，完全不推荐",
            "完全没有价值，不建议关注",
            "这根本解决不了问题",
        ]
    }

    AUTHORS = [
        "热心网友", "评论达人", "时评员", "观察者", "深度用户",
        "媒体人", "博主", "记者", "编辑", "专栏作家",
        "行业分析师", "研究员", "学者", "专家", "评论员"
    ]

    def __init__(self):
        """初始化模拟器"""
        self.sentiment_analyzer = SentimentAnalyzer()

    def generate_post(
        self,
        topic: Topic,
        platform: Optional[Platform] = None,
        sentiment: Optional[str] = None
    ) -> SocialPost:
        """
        生成模拟帖子

        Args:
            topic: 话题对象
            platform: 平台对象（可选，随机选择）
            sentiment: 情感倾向（可选，随机生成）

        Returns:
            SocialPost: 创建的帖子对象
        """
        if platform is None:
            # 从话题关联的平台中随机选择
            platforms = list(topic.platforms.filter(is_active=True))
            if not platforms:
                # 如果话题没有关联平台，获取所有活跃平台
                platforms = list(Platform.objects.filter(is_active=True))
            if not platforms:
                raise ValueError("没有可用的平台")
            platform = random.choice(platforms)

        # 选择情感倾向
        if sentiment is None:
            # 随机选择情感，但中性概率最高
            sentiment = random.choices(
                ['positive', 'neutral', 'negative'],
                weights=[0.3, 0.5, 0.2]
            )[0]

        # 生成内容
        content = random.choice(self.SAMPLE_CONTENTS[sentiment])

        # 添加话题相关关键词
        if topic.keywords:
            keyword = random.choice(topic.keywords)
            content = f"#{keyword}# {content}"

        # 生成作者
        author_prefix = random.choice(self.AUTHORS)
        author = f"{author_prefix}{random.randint(1000, 9999)}"

        # 生成发布时间（最近60分钟内）
        publish_time = timezone.now() - timedelta(
            minutes=random.randint(0, 60),
            seconds=random.randint(0, 59)
        )

        # 生成互动数据
        if sentiment == 'positive':
            # 正面内容通常有更多互动
            likes = random.randint(10, 5000)
            comments = random.randint(0, 500)
            shares = random.randint(0, 200)
            views = random.randint(likes * 2, 50000)
        elif sentiment == 'negative':
            # 负面内容也有较高互动
            likes = random.randint(0, 2000)
            comments = random.randint(10, 800)
            shares = random.randint(5, 300)
            views = random.randint(likes * 3, 80000)
        else:
            # 中性内容互动较少
            likes = random.randint(0, 500)
            comments = random.randint(0, 100)
            shares = random.randint(0, 50)
            views = random.randint(likes * 2, 10000)

        # 计算影响力分数
        influence_score = self._calculate_influence(
            likes, comments, shares, views, sentiment
        )

        # 情感分析
        sentiment_result = self.sentiment_analyzer.analyze(content)

        # 创建帖子
        post = SocialPost.objects.create(
            topic=topic,
            platform=platform,
            post_id=f"sim_{int(time.time())}_{random.randint(1000, 9999)}",
            content=content,
            author=author,
            publish_time=publish_time,
            likes=likes,
            comments=comments,
            shares=shares,
            views=views,
            sentiment=sentiment_result['sentiment'],
            sentiment_score=sentiment_result['sentiment_score'],
            keywords=sentiment_result['keywords'],
            influence_score=influence_score
        )

        return post

    def _calculate_influence(
        self,
        likes: int,
        comments: int,
        shares: int,
        views: int,
        sentiment: str
    ) -> float:
        """
        计算影响力分数

        综合考虑：
        - 点赞 (权重 0.3)
        - 评论 (权重 0.5) - 评论代表更深度的互动
        - 转发 (权重 0.8) - 转发代表扩散能力
        - 阅读 (权重 0.01)
        - 情感加成
        """
        base_score = (
            likes * 0.3 +
            comments * 0.5 +
            shares * 0.8 +
            views * 0.01
        )

        # 情感加成
        sentiment_multiplier = {
            'positive': 1.2,
            'neutral': 1.0,
            'negative': 1.3  # 负面内容通常有更高影响力
        }

        return base_score * sentiment_multiplier.get(sentiment, 1.0)

    def generate_batch(
        self,
        topic: Topic,
        count: int = 10
    ) -> List[SocialPost]:
        """
        批量生成帖子

        Args:
            topic: 话题对象
            count: 生成数量

        Returns:
            List[SocialPost]: 创建的帖子列表
        """
        posts = []
        platforms = list(topic.platforms.filter(is_active=True))

        if not platforms:
            platforms = list(Platform.objects.filter(is_active=True))

        for _ in range(count):
            platform = random.choice(platforms)
            post = self.generate_post(topic, platform)
            posts.append(post)

        return posts

    def generate_trend_posts(
        self,
        topic: Topic,
        hours: int = 24,
        posts_per_hour: int = 5
    ) -> List[SocialPost]:
        """
        生成趋势帖子（模拟时间分布）

        Args:
            topic: 话题对象
            hours: 过去几小时
            posts_per_hour: 每小时平均帖子数

        Returns:
            List[SocialPost]: 创建的帖子列表
        """
        posts = []
        platforms = list(topic.platforms.filter(is_active=True))

        if not platforms:
            platforms = list(Platform.objects.filter(is_active=True))

        now = timezone.now()

        for hour in range(hours):
            # 每小时帖子数量有波动
            count = random.randint(
                max(1, posts_per_hour - 2),
                posts_per_hour + 2
            )

            for _ in range(count):
                # 计算发布时间
                publish_time = now - timedelta(
                    hours=hour,
                    minutes=random.randint(0, 59)
                )

                # 生成帖子
                platform = random.choice(platforms)
                content = random.choice(
                    random.choice(list(self.SAMPLE_CONTENTS.values()))
                )
                author = f"{random.choice(self.AUTHORS)}{random.randint(1000, 9999)}"

                # 生成互动数据
                sentiment = random.choices(
                    ['positive', 'neutral', 'negative'],
                    weights=[0.3, 0.5, 0.2]
                )[0]

                if sentiment == 'positive':
                    likes = random.randint(10, 5000)
                    comments = random.randint(0, 500)
                    shares = random.randint(0, 200)
                elif sentiment == 'negative':
                    likes = random.randint(0, 2000)
                    comments = random.randint(10, 800)
                    shares = random.randint(5, 300)
                else:
                    likes = random.randint(0, 500)
                    comments = random.randint(0, 100)
                    shares = random.randint(0, 50)

                views = random.randint(likes * 2, 50000)
                influence_score = self._calculate_influence(
                    likes, comments, shares, views, sentiment
                )

                # 情感分析
                sentiment_result = self.sentiment_analyzer.analyze(content)

                # 创建帖子
                post = SocialPost.objects.create(
                    topic=topic,
                    platform=platform,
                    post_id=f"sim_{int(time.time())}_{random.randint(1000, 9999)}",
                    content=content,
                    author=author,
                    publish_time=publish_time,
                    likes=likes,
                    comments=comments,
                    shares=shares,
                    views=views,
                    sentiment=sentiment_result['sentiment'],
                    sentiment_score=sentiment_result['sentiment_score'],
                    keywords=sentiment_result['keywords'],
                    influence_score=influence_score
                )

                posts.append(post)

        return posts


class PostEngagementSimulator:
    """帖子互动模拟器（更新已有帖子的互动数据）"""

    @staticmethod
    def update_engagement(post: SocialPost, multiplier: float = 1.0):
        """
        更新帖子互动数据

        Args:
            post: 帖子对象
            multiplier: 增长倍数
        """
        # 随机增长
        likes_increase = int(random.randint(0, 10) * multiplier)
        comments_increase = int(random.randint(0, 5) * multiplier)
        shares_increase = int(random.randint(0, 3) * multiplier)
        views_increase = int(random.randint(10, 100) * multiplier)

        post.likes += likes_increase
        post.comments += comments_increase
        post.shares += shares_increase
        post.views += views_increase

        # 重新计算影响力
        post.influence_score = post.calculate_influence()
        post.save()

        return post
