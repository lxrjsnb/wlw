"""
帖子相关异步任务
"""
import random
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .services import SocialDataSimulator
from apps.topics.models import Topic, Platform
from apps.posts.models import SocialPost


@shared_task(name='posts.generate_simulated_posts')
def generate_simulated_posts(count_range=(5, 20)):
    """
    生成模拟帖子数据

    Args:
        count_range: 生成数量范围 (min, max)
    """
    try:
        # 获取活跃话题
        active_topics = Topic.objects.filter(status='active')

        if not active_topics.exists():
            return {'status': 'no_topics', 'message': '没有活跃话题'}

        # 获取活跃平台
        active_platforms = Platform.objects.filter(is_active=True)

        if not active_platforms.exists():
            return {'status': 'no_platforms', 'message': '没有活跃平台'}

        simulator = SocialDataSimulator()

        # 确定生成数量
        count = random.randint(*count_range)

        # 随机选择话题和平台
        created_posts = []
        for _ in range(count):
            topic = random.choice(active_topics)
            platform = random.choice(active_platforms)
            post = simulator.generate_post(topic, platform)
            created_posts.append({
                'id': post.id,
                'topic': topic.name,
                'platform': platform.name,
                'sentiment': post.sentiment
            })

        # 发送WebSocket通知（如果有channel layer）
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            for post_data in created_posts:
                # 向所有订阅该话题的用户推送
                async_to_sync(channel_layer.group_send)(
                    f'posts_topic_{topic.id}',
                    {
                        'type': 'new_post',
                        'data': post_data
                    }
                )
        except Exception as e:
            # WebSocket通知失败不影响主任务
            pass

        return {
            'status': 'success',
            'count': len(created_posts),
            'posts': created_posts
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='posts.update_post_engagement')
def update_post_engagement(hours=24, multiplier=1.0):
    """
    更新帖子互动数据

    Args:
        hours: 更新最近几小时的帖子
        multiplier: 增长倍数
    """
    try:
        # 获取最近发布的帖子
        since = timezone.now() - timedelta(hours=hours)
        posts = SocialPost.objects.filter(publish_time__gte=since)

        updated_count = 0
        for post in posts:
            # 随机决定是否更新（只更新部分帖子）
            if random.random() < 0.3:  # 30%概率更新
                from .services import PostEngagementSimulator
                PostEngagementSimulator.update_engagement(post, multiplier)
                updated_count += 1

        return {
            'status': 'success',
            'updated_count': updated_count
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='posts.cleanup_old_posts')
def cleanup_old_posts(days=90):
    """
    清理旧帖子数据（可选）

    Args:
        days: 保留最近几天的数据
    """
    try:
        # 删除超过指定天数的帖子
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = SocialPost.objects.filter(
            publish_time__lt=cutoff_date
        ).delete()[0]

        return {
            'status': 'success',
            'deleted_count': deleted_count
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='posts.generate_daily_summary')
def generate_daily_summary(date=None):
    """
    生成每日汇总数据

    Args:
        date: 汇总日期（默认为昨天）
    """
    try:
        from apps.posts.models import PostSummary
        from django.db.models import Count, Avg, Sum, Q

        if date is None:
            date = timezone.now().date() - timedelta(days=1)

        # 获取所有活跃话题
        topics = Topic.objects.filter(status='active')

        created_summaries = []

        for topic in topics:
            # 获取该话题当天的所有帖子
            posts = SocialPost.objects.filter(
                topic=topic,
                publish_time__date=date
            )

            if not posts.exists():
                continue

            # 按平台汇总
            for platform in Platform.objects.filter(is_active=True):
                platform_posts = posts.filter(platform=platform)

                if not platform_posts.exists():
                    continue

                # 检查是否已存在汇总
                summary, created = PostSummary.objects.get_or_create(
                    topic=topic,
                    platform=platform,
                    period='daily',
                    date=date,
                    hour=None
                )

                # 更新汇总数据
                summary.post_count = platform_posts.count()
                summary.total_likes = platform_posts.aggregate(Sum('likes'))['likes__sum'] or 0
                summary.total_comments = platform_posts.aggregate(Sum('comments'))['comments__sum'] or 0
                summary.total_shares = platform_posts.aggregate(Sum('shares'))['shares__sum'] or 0
                summary.total_views = platform_posts.aggregate(Sum('views'))['views__sum'] or 0

                # 情感统计
                summary.positive_count = platform_posts.filter(sentiment='positive').count()
                summary.neutral_count = platform_posts.filter(sentiment='neutral').count()
                summary.negative_count = platform_posts.filter(sentiment='negative').count()

                summary.avg_sentiment_score = platform_posts.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0
                summary.avg_influence_score = platform_posts.aggregate(Avg('influence_score'))['influence_score__avg'] or 0
                summary.max_influence_score = platform_posts.order_by('-influence_score').first().influence_score if platform_posts.exists() else 0

                summary.save()
                created_summaries.append(summary.id)

        return {
            'status': 'success',
            'created_count': len(created_summaries)
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
