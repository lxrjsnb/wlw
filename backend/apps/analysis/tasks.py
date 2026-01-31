"""
分析模块定时任务

使用Celery Beat定期执行:
- 热度计算 (每5分钟)
- 突发事件检测 (每分钟)
- KOL排行更新 (每小时)
- 演化阶段追踪 (每15分钟)
- 传播图构建 (每小时)
"""

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


@shared_task(name='analysis.update_hotness_scores')
def update_hotness_scores():
    """
    每5分钟更新热度分数

    计算所有帖子的热度分数并更新数据库
    """
    from .hotness_calculator import HotnessCalculator
    from apps.topics.models import Topic

    try:
        # 获取所有活跃话题
        active_topics = Topic.objects.filter(status='active')

        updated_count = 0
        for topic in active_topics:
            result = HotnessCalculator.update_all_hotness(topic.id)
            updated_count += result.get('updated', 0)

        logger.info(f'热度更新完成，共更新{updated_count}条帖子')
        return {
            'status': 'success',
            'updated_count': updated_count,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'热度更新失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='analysis.detect_emergency_events')
def detect_emergency_events():
    """
    每分钟检测突发事件

    对所有活跃话题进行突发事件检测
    """
    from .emergency_detector import EmergencyDetector
    from apps.topics.models import Topic

    try:
        # 获取所有活跃话题
        active_topics = Topic.objects.filter(status='active')

        total_detected = 0
        events_by_topic = {}

        for topic in active_topics:
            try:
                events = EmergencyDetector.detect_emergency_event(topic.id)
                if events:
                    total_detected += len(events)
                    events_by_topic[topic.name] = len(events)
            except Exception as e:
                logger.error(f'检测话题{topic.name}突发事件失败: {str(e)}')

        logger.info(f'突发事件检测完成，检测到{total_detected}个事件')

        return {
            'status': 'success',
            'total_detected': total_detected,
            'events_by_topic': events_by_topic,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'突发事件检测失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='analysis.update_kol_rankings')
def update_kol_rankings():
    """
    每小时更新KOL排行榜

    为所有活跃话题计算KOL得分和排行
    """
    from .kol_detector import KOLDetector
    from apps.topics.models import Topic

    try:
        # 获取所有活跃话题
        active_topics = Topic.objects.filter(status='active')

        results = []
        for topic in active_topics:
            try:
                result = KOLDetector.update_kol_rankings(topic.id)
                results.append({
                    'topic': topic.name,
                    'total': result.get('total', 0),
                    'created': result.get('created', 0),
                    'updated': result.get('updated', 0),
                })
            except Exception as e:
                logger.error(f'更新话题{topic.name}的KOL排行失败: {str(e)}')

        logger.info(f'KOL排行更新完成，处理了{len(results)}个话题')

        return {
            'status': 'success',
            'results': results,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'KOL排行更新失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='analysis.analyze_evolution_stage')
def analyze_evolution_stage():
    """
    每15分钟更新演化阶段

    检测话题是否发生阶段转换，更新演化数据
    """
    from .evolution_tracker import OpinionEvolutionTracker
    from apps.topics.models import Topic

    try:
        # 获取所有活跃话题
        active_topics = Topic.objects.filter(status='active')

        transitions = []
        for topic in active_topics:
            try:
                transition = OpinionEvolutionTracker.track_stage_transitions(topic.id)
                if transition and transition.get('transition'):
                    transitions.append({
                        'topic': topic.name,
                        'previous_stage': transition.get('previous_stage'),
                        'current_stage': transition.get('current_stage'),
                    })
            except Exception as e:
                logger.error(f'分析话题{topic.name}演化阶段失败: {str(e)}')

        logger.info(f'演化阶段分析完成，检测到{len(transitions)}次转换')

        return {
            'status': 'success',
            'transitions': transitions,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'演化阶段分析失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='analysis.build_propagation_graphs')
def build_propagation_graphs():
    """
    每小时构建传播图

    对近期活跃的帖子进行传播路径分析
    """
    from .propagation_analyzer import PropagationAnalyzer
    from apps.posts.models import SocialPost
    from django.utils import timezone
    from datetime import timedelta

    try:
        # 获取最近24小时的高热度帖子
        time_threshold = timezone.now() - timedelta(hours=24)
        hot_posts = SocialPost.objects.filter(
            publish_time__gte=time_threshold,
            influence_score__gte=50  # 热度>=50的帖子
        )[:50]  # 限制数量

        analyzed_count = 0
        for post in hot_posts:
            try:
                # 检查是否已有分析记录
                from .models import PropagationPath
                existing = PropagationPath.objects.filter(post=post).exists()

                if not existing:
                    result = PropagationAnalyzer.analyze_propagation(post.id)
                    if result:
                        analyzed_count += 1
            except Exception as e:
                logger.error(f'分析帖子{post.id}传播路径失败: {str(e)}')

        logger.info(f'传播图构建完成，分析了{analyzed_count}个帖子')

        return {
            'status': 'success',
            'analyzed_count': analyzed_count,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'传播图构建失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='analysis.create_sentiment_snapshots')
def create_sentiment_snapshots():
    """
    每小时创建情感快照

    为所有活跃话题创建当前时刻的情感分布快照
    """
    from .sentiment_analyzer import SentimentAnalyzer
    from apps.topics.models import Topic

    try:
        # 获取所有活跃话题
        active_topics = Topic.objects.filter(status='active')

        snapshots_created = 0
        for topic in active_topics:
            try:
                # 只对有新帖子的话题创建快照
                from apps.posts.models import SocialPost
                recent_posts = SocialPost.objects.filter(
                    topic=topic,
                    publish_time__gte=timezone.now() - timedelta(hours=1)
                ).exists()

                if recent_posts:
                    snapshot = SentimentAnalyzer.create_sentiment_snapshot(topic.id)
                    if snapshot:
                        snapshots_created += 1
            except Exception as e:
                logger.error(f'创建话题{topic.name}情感快照失败: {str(e)}')

        logger.info(f'情感快照创建完成，创建了{snapshots_created}个快照')

        return {
            'status': 'success',
            'snapshots_created': snapshots_created,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'情感快照创建失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


@shared_task(name='analysis.update_topic_baselines')
def update_topic_baselines():
    """
    每天更新话题基线数据

    用于异常检测的历史基线数据更新
    """
    from .evolution_tracker import OpinionEvolutionTracker
    from apps.topics.models import Topic

    try:
        # 获取所有活跃话题
        active_topics = Topic.objects.filter(status='active')

        updated_count = 0
        for topic in active_topics:
            try:
                success = OpinionEvolutionTracker.update_baseline(topic.id)
                if success:
                    updated_count += 1
            except Exception as e:
                logger.error(f'更新话题{topic.name}基线失败: {str(e)}')

        logger.info(f'话题基线更新完成，更新了{updated_count}个话题')

        return {
            'status': 'success',
            'updated_count': updated_count,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'话题基线更新失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }


# 便捷任务：综合更新（可手动触发）
@shared_task(name='analysis.full_update')
def full_update(topic_id=None):
    """
    执行完整的数据更新

    Args:
        topic_id: 指定话题ID，None表示所有话题
    """
    from apps.topics.models import Topic

    try:
        if topic_id:
            topics = [Topic.objects.get(id=topic_id)]
        else:
            topics = Topic.objects.filter(status='active')

        results = []

        for topic in topics:
            result = {
                'topic': topic.name,
                'topic_id': topic.id,
            }

            # 1. 更新热度
            from .hotness_calculator import HotnessCalculator
            hotness_result = HotnessCalculator.update_all_hotness(topic.id)
            result['hotness'] = hotness_result

            # 2. 更新KOL
            from .kol_detector import KOLDetector
            kol_result = KOLDetector.update_kol_rankings(topic.id)
            result['kol'] = kol_result

            # 3. 检测突发事件
            from .emergency_detector import EmergencyDetector
            emergency_events = EmergencyDetector.detect_emergency_event(topic.id)
            result['emergency'] = {'detected': len(emergency_events)}

            # 4. 更新演化阶段
            from .evolution_tracker import OpinionEvolutionTracker
            evolution = OpinionEvolutionTracker.track_stage_transitions(topic.id)
            result['evolution'] = evolution

            # 5. 更新基线
            baseline_updated = OpinionEvolutionTracker.update_baseline(topic.id)
            result['baseline'] = {'updated': baseline_updated}

            results.append(result)

        logger.info(f'完整更新完成，处理了{len(results)}个话题')

        return {
            'status': 'success',
            'results': results,
            'timestamp': timezone.now().isoformat(),
        }
    except Exception as e:
        logger.error(f'完整更新失败: {str(e)}')
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': timezone.now().isoformat(),
        }
