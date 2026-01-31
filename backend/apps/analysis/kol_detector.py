"""
KOL（关键意见领袖）识别模块

四维影响力评分:
1. 内容影响力 (40%): 平均互动量、爆款率
2. 网络影响力 (30%): PageRank、中心性指标
3. 话题引领力 (20%): 时间领先性、引用次数
4. 情感影响力 (10%): 情感传染率、引导力
"""

import networkx as nx
from django.db.models import Q, Count, Avg, Sum, Max, F, ExpressionWrapper, FloatField
from django.db.models.functions import Cast
from django.utils import timezone
from collections import defaultdict
from apps.posts.models import SocialPost
from apps.topics.models import Topic
from apps.analysis.models import KOLProfile


class KOLDetector:
    """KOL识别器"""

    # 权重配置
    WEIGHTS = {
        'content': 0.4,
        'network': 0.3,
        'leadership': 0.2,
        'sentiment': 0.1,
    }

    # 互动权重
    INTERACTION_WEIGHTS = {
        'likes': 1.0,
        'comments': 3.0,
        'shares': 5.0,
    }

    # KOL类型阈值
    KOL_TYPE_THRESHOLDS = {
        'initiator': {      # 发起者: 高引领力
            'leadership_min': 0.7,
            'content_min': 0.5,
        },
        'spreader': {       # 传播者: 高网络影响力
            'network_min': 0.7,
            'content_min': 0.5,
        },
        'guide': {          # 引导者: 高情感影响力
            'sentiment_min': 0.7,
            'network_min': 0.5,
        },
        'comprehensive': {  # 综合影响力者: 各维度均衡且高分
            'overall_min': 0.7,
            'balance_max': 0.3,  # 各维度差异不超过0.3
        },
    }

    @classmethod
    def calculate_kol_score(cls, author, topic_id):
        """
        计算KOL综合得分

        Args:
            author: 作者名
            topic_id: 话题ID

        Returns:
            dict: KOL得分和各维度得分
        """
        # 获取该作者在该话题下的所有帖子
        posts = SocialPost.objects.filter(
            topic_id=topic_id,
            author=author
        )

        if not posts.exists():
            return cls._get_default_kol_score(author)

        # 1. 内容影响力
        content_score = cls._calculate_content_influence(posts)

        # 2. 网络影响力
        network_score = cls._calculate_network_influence(author, topic_id, posts)

        # 3. 话题引领力
        leadership_score = cls._calculate_topic_leadership(posts, topic_id)

        # 4. 情感影响力
        sentiment_score = cls._calculate_sentiment_influence(posts)

        # 综合得分
        kol_score = (
            content_score * cls.WEIGHTS['content'] +
            network_score * cls.WEIGHTS['network'] +
            leadership_score * cls.WEIGHTS['leadership'] +
            sentiment_score * cls.WEIGHTS['sentiment']
        )

        # 归一化到0-100
        kol_score_normalized = min(max(kol_score * 100, 0), 100)

        return {
            'author': author,
            'kol_score': round(kol_score_normalized, 2),
            'content_influence': round(content_score, 4),
            'network_influence': round(network_score, 4),
            'topic_leadership': round(leadership_score, 4),
            'sentiment_influence': round(sentiment_score, 4),
        }

    @classmethod
    def _get_default_kol_score(cls, author):
        """返回默认KOL得分"""
        return {
            'author': author,
            'kol_score': 0,
            'content_influence': 0,
            'network_influence': 0,
            'topic_leadership': 0,
            'sentiment_influence': 0,
        }

    @classmethod
    def _calculate_content_influence(cls, posts):
        """
        计算内容影响力 (40%)

        考虑因素:
        - 平均互动量
        - 爆款率 (热度>90的帖子占比)
        - 内容质量 (长度、媒体丰富度)
        """
        # 计算平均互动量
        avg_stats = posts.aggregate(
            avg_likes=Avg('likes'),
            avg_comments=Avg('comments'),
            avg_shares=Avg('shares'),
        )

        avg_engagement = (
            (avg_stats['avg_likes'] or 0) * cls.INTERACTION_WEIGHTS['likes'] +
            (avg_stats['avg_comments'] or 0) * cls.INTERACTION_WEIGHTS['comments'] +
            (avg_stats['avg_shares'] or 0) * cls.INTERACTION_WEIGHTS['shares']
        )

        # 归一化互动量（使用对数缩放）
        import math
        normalized_engagement = min(math.log1p(avg_engagement) / 10, 1)

        # 爆款率
        total = posts.count()
        viral_count = posts.filter(influence_score__gte=90).count()
        viral_rate = viral_count / total if total > 0 else 0

        # 内容质量因子（平均内容长度）
        avg_length = posts.aggregate(avg_len=Avg(Cast('content', output_field=FloatField())))['avg_len'] or 0
        quality_factor = min(math.log1p(avg_length) / 10, 1.2)

        # 综合内容影响力
        content_score = normalized_engagement * 0.6 + viral_rate * 0.3 + (quality_factor - 1) * 0.1

        return min(max(content_score, 0), 1)

    @classmethod
    def _calculate_network_influence(cls, author, topic_id, posts):
        """
        计算网络影响力 (30%)

        考虑因素:
        - PageRank得分
        - 介数中心性
        - 接近中心性
        """
        # 构建传播图（简化：基于帖子互动关系）
        graph = cls._build_author_graph(topic_id)

        if author not in graph:
            # 如果图中没有该作者，使用粉丝数和互动量估算
            total_interactions = posts.aggregate(
                total=Sum(F('likes') + F('comments') + F('shares'))
            )['total'] or 0

            import math
            return min(math.log1p(total_interactions) / 20, 0.5)

        try:
            # PageRank
            pagerank = nx.pagerank(graph, weight='weight')
            pr_score = pagerank.get(author, 0)

            # 归一化PageRank（乘以节点数使其范围合理）
            normalized_pr = min(pr_score * graph.number_of_nodes(), 1)

            # 介数中心性
            betweenness = nx.betweenness_centrality(graph, weight='weight')
            bc_score = betweenness.get(author, 0)

            # 综合网络影响力
            network_score = normalized_pr * 0.7 + bc_score * 0.3

            return min(max(network_score, 0), 1)

        except:
            return 0.5

    @classmethod
    def _build_author_graph(cls, topic_id):
        """构建作者关系图"""
        # 获取话题下所有帖子
        posts = SocialPost.objects.filter(topic_id=topic_id)

        # 创建图
        G = nx.DiGraph()

        # 添加节点（作者）
        authors = set(posts.values_list('author', flat=True))
        for author in authors:
            G.add_node(author)

        # 添加边（基于互动关系）
        # 简化策略：如果作者A的帖子被很多人评论，认为A是影响力节点
        author_stats = posts.values('author').annotate(
            total_interactions=Sum(F('likes') + F('comments') + F('shares'))
        )

        max_interactions = max(
            [s['total_interactions'] or 0 for s in author_stats],
            default=1
        )

        for stat in author_stats:
            author = stat['author']
            interactions = stat['total_interactions'] or 0
            # 归一化影响力
            normalized_influence = interactions / max_interactions if max_interactions > 0 else 0

            # 更新节点属性
            if G.has_node(author):
                G.nodes[author]['influence'] = normalized_influence

        # 添加边（基于转发关系推断）
        # 简化：如果作者B在作者A发帖后短时间内发帖，可能存在传播关系
        post_list = list(posts.order_by('publish_time'))

        for i, post_a in enumerate(post_list):
            for post_b in post_list[i + 1:i + 20]:  # 只检查后续20条
                if post_b.publish_time and post_a.publish_time:
                    time_diff = (post_b.publish_time - post_a.publish_time).total_seconds()
                    if time_diff < 3600:  # 1小时内
                        weight = 1 - time_diff / 3600
                        G.add_edge(post_a.author, post_b.author, weight=weight)

        return G

    @classmethod
    def _calculate_topic_leadership(cls, posts, topic_id):
        """
        计算话题引领力 (20%)

        考虑因素:
        - 时间领先性（首发时间与话题热度峰值的时差）
        - 引用次数（其他帖子引用该用户帖子的次数）
        - 发起率（发起话题数 / 参与话题数）
        """
        if not posts.exists():
            return 0

        # 1. 时间领先性
        first_post = posts.order_by('publish_time').first()
        if not first_post or not first_post.publish_time:
            time_leadership = 0
        else:
            # 计算该话题的热度峰值时间
            topic_posts = SocialPost.objects.filter(topic_id=topic_id)
            peak_post = topic_posts.order_by('-influence_score').first()

            if peak_post and peak_post.publish_time and first_post.publish_time < peak_post.publish_time:
                time_diff = (peak_post.publish_time - first_post.publish_time).total_seconds() / 3600  # 小时
                # 越早发帖，引领力越高
                time_leadership = max(0, 1 - time_diff / 24)  # 24小时内衰减
            else:
                time_leadership = 0

        # 2. 发起率（该作者帖子数占话题总帖子数的比例）
        total_topic_posts = topic_posts.count()
        author_posts = posts.count()
        initiation_rate = author_posts / total_topic_posts if total_topic_posts > 0 else 0

        # 归一化（假设占1%以上即为高引领力）
        normalized_initiation = min(initiation_rate * 100, 1)

        # 综合引领力
        leadership_score = time_leadership * 0.7 + normalized_initiation * 0.3

        return min(max(leadership_score, 0), 1)

    @classmethod
    def _calculate_sentiment_influence(cls, posts):
        """
        计算情感影响力 (10%)

        考虑因素:
        - 情感传染率（跟帖情感与原帖情感一致的比例）
        - 情感引导力（后续讨论的情感倾向与该用户的相关性）
        """
        if not posts.exists():
            return 0

        # 简化实现：基于帖子的平均情感强度和互动量
        avg_sentiment = posts.aggregate(avg=Avg('sentiment_score'))['avg'] or 0

        # 情感强度（绝对值越大，情感越鲜明）
        sentiment_intensity = abs(avg_sentiment)

        # 高互动帖子的情感传染力
        high_engagement_posts = posts.filter(
            likes__gt=10
        ) | posts.filter(
            comments__gt=5
        ) | posts.filter(
            shares__gt=5
        )

        if high_engagement_posts.exists():
            high_engagement_sentiment = high_engagement_posts.aggregate(
                avg=Avg('sentiment_score')
            )['avg'] or 0
           传染力 = abs(high_engagement_sentiment)
        else:
            传染力 = 0

        # 综合情感影响力
        sentiment_score = sentiment_intensity * 0.5 + 传染力 * 0.5

        return min(max(sentiment_score, 0), 1)

    @classmethod
    def classify_kol_type(cls, kol_scores):
        """
        KOL类型分类

        Args:
            kol_scores: KOL得分字典

        Returns:
            str: KOL类型
        """
        content = kol_scores.get('content_influence', 0)
        network = kol_scores.get('network_influence', 0)
        leadership = kol_scores.get('topic_leadership', 0)
        sentiment = kol_scores.get('sentiment_influence', 0)

        # 计算各维度差异
        scores = [content, network, leadership, sentiment]
        max_score = max(scores)
        min_score = min(scores)
        balance = max_score - min_score

        # 检查各类型条件
        # 综合影响力者：各维度均衡且高分
        if (kol_scores.get('kol_score', 0) >= 70 and
            balance < cls.KOL_TYPE_THRESHOLDS['comprehensive']['balance_max']):
            return 'comprehensive'

        # 发起者：高引领力
        if (leadership >= cls.KOL_TYPE_THRESHOLDS['initiator']['leadership_min'] and
            content >= cls.KOL_TYPE_THRESHOLDS['initiator']['content_min']):
            return 'initiator'

        # 传播者：高网络影响力
        if (network >= cls.KOL_TYPE_THRESHOLDS['spreader']['network_min'] and
            content >= cls.KOL_TYPE_THRESHOLDS['spreader']['content_min']):
            return 'spreader'

        # 引导者：高情感影响力
        if (sentiment >= cls.KOL_TYPE_THRESHOLDS['guide']['sentiment_min'] and
            network >= cls.KOL_TYPE_THRESHOLDS['guide']['network_min']):
            return 'guide'

        # 默认为综合影响力者
        return 'comprehensive'

    @classmethod
    def update_kol_rankings(cls, topic_id):
        """
        更新话题的KOL排行榜

        Args:
            topic_id: 话题ID

        Returns:
            dict: 更新统计
        """
        # 获取话题下所有作者
        authors = SocialPost.objects.filter(
            topic_id=topic_id
        ).values_list('author', flat=True).distinct()

        updated_count = 0
        created_count = 0

        for author in authors:
            # 计算KOL得分
            scores = cls.calculate_kol_score(author, topic_id)

            # 确定KOL类型
            kol_type = cls.classify_kol_type(scores)

            # 获取或创建KOLProfile
            profile, created = KOLProfile.objects.get_or_create(
                author=author,
                topic_id=topic_id,
                defaults={
                    'kol_type': kol_type,
                    'kol_score': scores['kol_score'],
                    'content_influence': scores['content_influence'],
                    'network_influence': scores['network_influence'],
                    'topic_leadership': scores['topic_leadership'],
                    'sentiment_influence': scores['sentiment_influence'],
                }
            )

            if not created:
                # 更新现有记录
                profile.kol_type = kol_type
                profile.kol_score = scores['kol_score']
                profile.content_influence = scores['content_influence']
                profile.network_influence = scores['network_influence']
                profile.topic_leadership = scores['topic_leadership']
                profile.sentiment_influence = scores['sentiment_influence']

                # 更新统计数据
                posts = SocialPost.objects.filter(topic_id=topic_id, author=author)
                stats = posts.aggregate(
                    post_count=Count('id'),
                    total_likes=Sum('likes'),
                    total_comments=Sum('comments'),
                    total_shares=Sum('shares'),
                    avg_sentiment=Avg('sentiment_score'),
                )

                profile.post_count = stats['post_count'] or 0
                profile.total_likes = stats['total_likes'] or 0
                profile.total_comments = stats['total_comments'] or 0
                profile.total_shares = stats['total_shares'] or 0
                profile.avg_sentiment_score = stats['avg_sentiment'] or 0

                profile.save()
                updated_count += 1
            else:
                # 新建记录
                posts = SocialPost.objects.filter(topic_id=topic_id, author=author)
                stats = posts.aggregate(
                    post_count=Count('id'),
                    total_likes=Sum('likes'),
                    total_comments=Sum('comments'),
                    total_shares=Sum('shares'),
                    avg_sentiment=Avg('sentiment_score'),
                )

                profile.post_count = stats['post_count'] or 0
                profile.total_likes = stats['total_likes'] or 0
                profile.total_comments = stats['total_comments'] or 0
                profile.total_shares = stats['total_shares'] or 0
                profile.avg_sentiment_score = stats['avg_sentiment'] or 0

                profile.save()
                created_count += 1

        return {
            'total': len(authors),
            'created': created_count,
            'updated': updated_count,
            'topic_id': topic_id,
        }

    @classmethod
    def get_top_kols(cls, topic_id, limit=20, sort_by='kol_score'):
        """
        获取Top KOL列表

        Args:
            topic_id: 话题ID
            limit: 返回数量
            sort_by: 排序字段 (kol_score/content_influence/network_influence/topic_leadership/sentiment_influence)

        Returns:
            list: KOL列表
        """
        # 确保排序字段有效
        valid_sort_fields = [
            'kol_score', 'content_influence', 'network_influence',
            'topic_leadership', 'sentiment_influence'
        ]
        if sort_by not in valid_sort_fields:
            sort_by = 'kol_score'

        kols = KOLProfile.objects.filter(
            topic_id=topic_id
        ).order_by(f'-{sort_by}')[:limit]

        return list(kols)

    @classmethod
    def get_kol_profile(cls, topic_id, author):
        """
        获取KOL画像

        Args:
            topic_id: 话题ID
            author: 作者名

        Returns:
            KOLProfile: KOL画像对象
        """
        try:
            return KOLProfile.objects.get(topic_id=topic_id, author=author)
        except KOLProfile.DoesNotExist:
            return None

    @classmethod
    def get_kol_type_distribution(cls, topic_id):
        """
        获取KOL类型分布

        Args:
            topic_id: 话题ID

        Returns:
            dict: 各类型KOL的数量和占比
        """
        profiles = KOLProfile.objects.filter(topic_id=topic_id)
        total = profiles.count()

        distribution = {}
        for type_code, type_label in KOLProfile.KOL_TYPE_CHOICES:
            count = profiles.filter(kol_type=type_code).count()
            distribution[type_code] = {
                'label': type_label,
                'count': count,
                'percentage': round(count / total * 100, 2) if total > 0 else 0,
            }

        return distribution


# 便捷函数
def calculate_author_kol_score(author, topic_id):
    """计算作者KOL得分的便捷函数"""
    return KOLDetector.calculate_kol_score(author, topic_id)


def update_topic_kols(topic_id):
    """更新话题KOL排行榜的便捷函数"""
    return KOLDetector.update_kol_rankings(topic_id)
