"""
舆情演化阶段追踪模块

六阶段生命周期模型:
1. 潜伏期 (latent): 帖子少、情感中性
2. 萌发期 (germination): 增长率>20%
3. 爆发期 (explosion): 帖子数>均值×3
4. 扩散期 (diffusion): 增长放缓
5. 衰退期 (decline): 连续3h下降
6. 消亡期 (death): 帖子数<峰值×0.1

功能:
- 阶段分类识别
- 阶段转换检测
- 基线数据更新
- 下一阶段预测
"""

from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, Max, Min, StdDev, F
from django.utils import timezone
from collections import defaultdict
import numpy as np
from apps.posts.models import SocialPost, PostSummary
from apps.topics.models import Topic
from apps.analysis.models import OpinionEvolution


class OpinionEvolutionTracker:
    """舆情演化追踪器"""

    # 阶段阈值配置
    STAGE_THRESHOLDS = {
        'latent': {
            'post_ratio_max': 1.2,  # 帖子数 < 历史均值×1.2
            'description': '潜伏期：少量帖子、情感中性',
        },
        'germination': {
            'growth_rate_min': 0.2,  # 增长率 > 20%
            'description': '萌发期：开始快速增长',
        },
        'explosion': {
            'post_ratio_min': 3.0,  # 帖子数 > 历史均值×3
            'description': '爆发期：指数级增长',
        },
        'diffusion': {
            'growth_rate_max': 0.2,  # 0 < 增长率 < 20%
            'growth_rate_min': 0.0,
            'description': '扩散期：增长放缓',
        },
        'decline': {
            'decline_hours': 3,  # 连续3小时下降
            'description': '衰退期：持续下降',
        },
        'death': {
            'post_ratio_peak': 0.1,  # 帖子数 < 峰值×0.1
            'description': '消亡期：基本沉寂',
        },
    }

    # 阶段顺序
    STAGE_ORDER = [
        'latent',
        'germination',
        'explosion',
        'diffusion',
        'decline',
        'death',
    ]

    @classmethod
    def classify_evolution_stage(cls, topic_id):
        """
        分类当前演化阶段

        Args:
            topic_id: 话题ID

        Returns:
            dict: 阶段信息
        """
        # 获取话题
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return None

        # 获取时间序列数据（过去7天）
        now = timezone.now()
        start_time = now - timedelta(days=7)

        # 按小时聚合数据
        hourly_data = cls._get_hourly_data(topic_id, start_time, now)

        if not hourly_data:
            # 没有数据，默认潜伏期
            return cls._create_stage_info(topic, 'latent', {})

        # 计算指标
        metrics = cls._calculate_stage_metrics(hourly_data)

        # 获取历史基线
        baseline = cls._get_baseline(topic_id)

        # 判断阶段
        current_stage = cls._determine_stage(metrics, baseline)

        # 获取峰值热度
        peak_hotness = cls._get_peak_hotness(topic_id, start_time, now)

        stage_info = cls._create_stage_info(topic, current_stage, metrics)
        stage_info['peak_hotness'] = peak_hotness

        return stage_info

    @classmethod
    def _get_hourly_data(cls, topic_id, start_time, end_time):
        """按小时聚合帖子数据"""
        posts = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__gte=start_time,
            publish_time__lte=end_time
        ).order_by('publish_time')

        hourly_counts = defaultdict(int)
        hourly_sentiment = defaultdict(list)

        for post in posts:
            if post.publish_time:
                hour_key = post.publish_time.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour_key] += 1
                if post.sentiment_score:
                    hourly_sentiment[hour_key].append(post.sentiment_score)

        # 整理数据
        data = []
        for hour in sorted(hourly_counts.keys()):
            data.append({
                'hour': hour,
                'post_count': hourly_counts[hour],
                'avg_sentiment': np.mean(hourly_sentiment[hour]) if hourly_sentiment[hour] else 0,
            })

        return data

    @classmethod
    def _calculate_stage_metrics(cls, hourly_data):
        """计算阶段判断所需指标"""
        if not hourly_data:
            return {}

        # 当前小时的帖子数
        current_count = hourly_data[-1]['post_count'] if hourly_data else 0

        # 历史均值（过去24小时）
        recent_data = hourly_data[-24:] if len(hourly_data) >= 24 else hourly_data
        historical_mean = np.mean([d['post_count'] for d in recent_data]) if recent_data else 1

        # 当前帖子数与历史均值的比率
        post_ratio = current_count / historical_mean if historical_mean > 0 else 0

        # 增长率（最近1小时 vs 前1小时）
        if len(hourly_data) >= 2:
            prev_count = hourly_data[-2]['post_count']
            growth_rate = (current_count - prev_count) / prev_count if prev_count > 0 else 0
        else:
            growth_rate = 0

        # 连续下降小时数
        decline_hours = 0
        for i in range(len(hourly_data) - 1, 0, -1):
            if hourly_data[i]['post_count'] < hourly_data[i - 1]['post_count']:
                decline_hours += 1
            else:
                break

        # 峰值帖子数
        peak_count = max([d['post_count'] for d in hourly_data]) if hourly_data else 1
        peak_ratio = current_count / peak_count if peak_count > 0 else 0

        # 平均情感
        avg_sentiment = np.mean([d['avg_sentiment'] for d in hourly_data[-24:]]) if hourly_data else 0

        return {
            'current_count': current_count,
            'historical_mean': round(historical_mean, 2),
            'post_ratio': round(post_ratio, 2),
            'growth_rate': round(growth_rate, 4),
            'decline_hours': decline_hours,
            'peak_count': peak_count,
            'peak_ratio': round(peak_ratio, 2),
            'avg_sentiment': round(avg_sentiment, 3),
            'data_points': len(hourly_data),
        }

    @classmethod
    def _determine_stage(cls, metrics, baseline):
        """根据指标确定阶段"""
        current_count = metrics.get('current_count', 0)
        post_ratio = metrics.get('post_ratio', 0)
        growth_rate = metrics.get('growth_rate', 0)
        decline_hours = metrics.get('decline_hours', 0)
        peak_ratio = metrics.get('peak_ratio', 0)

        # 优先判断极端情况

        # 消亡期：帖子数极少
        if peak_ratio < cls.STAGE_THRESHOLDS['death']['post_ratio_peak'] and current_count < 5:
            return 'death'

        # 爆发期：帖子数远超历史均值
        if post_ratio >= cls.STAGE_THRESHOLDS['explosion']['post_ratio_min']:
            return 'explosion'

        # 衰退期：连续下降
        if decline_hours >= cls.STAGE_THRESHOLDS['decline']['decline_hours']:
            return 'decline'

        # 萌发期：快速增长
        if growth_rate >= cls.STAGE_THRESHOLDS['germination']['growth_rate_min']:
            return 'germination'

        # 扩散期：缓慢增长
        if 0 < growth_rate < cls.STAGE_THRESHOLDS['diffusion']['growth_rate_max']:
            return 'diffusion'

        # 默认潜伏期
        return 'latent'

    @classmethod
    def _create_stage_info(cls, topic, stage, metrics):
        """创建阶段信息"""
        return {
            'topic_id': topic.id,
            'topic_name': topic.name,
            'stage': stage,
            'stage_label': dict(OpinionEvolution.STAGE_CHOICES).get(stage, '未知'),
            'description': cls.STAGE_THRESHOLDS.get(stage, {}).get('description', ''),
            'metrics': metrics,
            'timestamp': timezone.now().isoformat(),
        }

    @classmethod
    def _get_peak_hotness(cls, topic_id, start_time, end_time):
        """获取峰值热度"""
        peak = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__gte=start_time,
            publish_time__lte=end_time
        ).order_by('-influence_score').first()

        return peak.influence_score if peak else 0

    @classmethod
    def _get_baseline(cls, topic_id):
        """获取历史基线数据"""
        # 获取过去30天的数据作为基线
        end_time = timezone.now()
        start_time = end_time - timedelta(days=30)

        baseline = PostSummary.objects.filter(
            topic_id=topic_id,
            date__gte=start_time.date(),
            date__lte=end_time.date(),
            period='daily'
        ).aggregate(
            avg_posts=Avg('post_count'),
            avg_hotness=Avg('avg_influence_score'),
            max_posts=Max('post_count'),
        )

        return {
            'avg_posts': round(baseline['avg_posts'] or 0, 2),
            'avg_hotness': round(baseline['avg_hotness'] or 0, 2),
            'max_posts': baseline['max_posts'] or 0,
        }

    @classmethod
    def track_stage_transitions(cls, topic_id):
        """
        跟踪阶段转换

        检测话题是否从一个阶段转换到另一个阶段

        Args:
            topic_id: 话题ID

        Returns:
            dict: 转换信息
        """
        # 获取当前阶段
        current_stage_info = cls.classify_evolution_stage(topic_id)
        if not current_stage_info:
            return None

        current_stage = current_stage_info['stage']

        # 获取上一阶段记录
        last_stage = OpinionEvolution.objects.filter(
            topic_id=topic_id
        ).order_by('-started_at').first()

        if last_stage and last_stage.stage == current_stage:
            # 阶段未变化
            return {
                'transition': False,
                'current_stage': current_stage,
                'stage_label': current_stage_info['stage_label'],
                'duration_hours': (timezone.now() - last_stage.started_at).total_seconds() / 3600,
            }

        # 阶段发生变化，创建新记录
        transition_info = cls._create_stage_transition(
            topic_id, current_stage, current_stage_info, last_stage
        )

        return transition_info

    @classmethod
    def _create_stage_transition(cls, topic_id, new_stage, stage_info, last_stage):
        """创建阶段转换记录"""
        topic = Topic.objects.get(id=topic_id)

        # 如果有上一阶段，更新其结束时间
        if last_stage:
            last_stage.ended_at = timezone.now()
            last_stage.duration_hours = (
                last_stage.ended_at - last_stage.started_at
            ).total_seconds() / 3600
            last_stage.save()

        # 创建新阶段记录
        metrics = stage_info.get('metrics', {})

        new_evolution = OpinionEvolution.objects.create(
            topic=topic,
            stage=new_stage,
            peak_hotness=stage_info.get('peak_hotness', 0),
            post_count=metrics.get('current_count', 0),
            avg_sentiment=metrics.get('avg_sentiment', 0),
            transition_metrics=metrics,
        )

        # 预测下一阶段
        prediction = cls.predict_next_stage(topic_id)
        if prediction:
            new_evolution.predicted_next_stage = prediction.get('next_stage', '')
            new_evolution.predicted_duration = prediction.get('predicted_duration', 0)
            new_evolution.confidence = prediction.get('confidence', 0)
            new_evolution.save()

        return {
            'transition': True,
            'previous_stage': last_stage.stage if last_stage else None,
            'current_stage': new_stage,
            'current_stage_label': stage_info['stage_label'],
            'evolution_id': new_evolution.id,
            'prediction': prediction,
        }

    @classmethod
    def predict_next_stage(cls, topic_id):
        """
        预测下一阶段

        基于历史数据和当前阶段进行预测

        Args:
            topic_id: 话题ID

        Returns:
            dict: 预测信息
        """
        current_info = cls.classify_evolution_stage(topic_id)
        if not current_info:
            return None

        current_stage = current_info['stage']

        # 获取历史阶段持续时间
        historical_durations = OpinionEvolution.objects.filter(
            topic_id=topic_id,
            stage=current_stage
        ).exclude(
            duration_hours__isnull=True
        ).values_list('duration_hours', flat=True)

        # 预测下一阶段
        current_index = cls.STAGE_ORDER.index(current_stage)

        # 特殊逻辑：消亡期是最后阶段
        if current_stage == 'death':
            return {
                'next_stage': 'death',
                'predicted_duration': 0,
                'confidence': 1.0,
                'note': '已到达最后阶段',
            }

        # 简单预测：下一阶段是顺序中的下一个
        if current_index < len(cls.STAGE_ORDER) - 1:
            next_stage = cls.STAGE_ORDER[current_index + 1]
        else:
            next_stage = 'death'

        # 预测持续时间（基于历史平均）
        if historical_durations:
            avg_duration = np.mean(historical_durations)
            std_duration = np.std(historical_durations)
            predicted_duration = avg_duration
            # 置信度基于标准差（标准差越小，置信度越高）
            confidence = max(0, min(1, 1 - std_duration / (avg_duration + 1)))
        else:
            # 使用默认持续时间
            default_durations = {
                'latent': 48,
                'germination': 12,
                'explosion': 24,
                'diffusion': 48,
                'decline': 72,
                'death': 168,
            }
            predicted_duration = default_durations.get(current_stage, 24)
            confidence = 0.5  # 默认置信度

        return {
            'current_stage': current_stage,
            'next_stage': next_stage,
            'next_stage_label': dict(OpinionEvolution.STAGE_CHOICES).get(next_stage, '未知'),
            'predicted_duration': round(predicted_duration, 2),
            'confidence': round(confidence, 2),
        }

    @classmethod
    def update_baseline(cls, topic_id):
        """
        更新基线数据

        将当前阶段数据添加到基线中

        Args:
            topic_id: 话题ID

        Returns:
            bool: 是否成功
        """
        # 确保PostSummary中有最新的数据
        now = timezone.now()
        today = now.date()

        # 创建或更新今日汇总
        summary, created = PostSummary.objects.get_or_create(
            topic_id=topic_id,
            period='daily',
            date=today,
            defaults={}
        )

        # 更新统计数据
        posts = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__date=today
        )

        stats = posts.aggregate(
            post_count=Count('id'),
            total_likes=Sum('likes'),
            total_comments=Sum('comments'),
            total_shares=Sum('shares'),
            avg_sentiment=Avg('sentiment_score'),
            avg_influence=Avg('influence_score'),
            max_influence=Max('influence_score'),
        )

        summary.post_count = stats['post_count'] or 0
        summary.total_likes = stats['total_likes'] or 0
        summary.total_comments = stats['total_comments'] or 0
        summary.total_shares = stats['total_shares'] or 0
        summary.avg_sentiment_score = stats['avg_sentiment'] or 0
        summary.avg_influence_score = stats['avg_influence'] or 0
        summary.max_influence_score = stats['max_influence'] or 0
        summary.save()

        return True

    @classmethod
    def get_evolution_history(cls, topic_id, limit=50):
        """
        获取演化历史

        Args:
            topic_id: 话题ID
            limit: 返回记录数

        Returns:
            list: 演化历史记录
        """
        history = OpinionEvolution.objects.filter(
            topic_id=topic_id
        ).order_by('-started_at')[:limit]

        result = []
        for record in history:
            result.append({
                'id': record.id,
                'stage': record.stage,
                'stage_label': record.get_stage_display(),
                'started_at': record.started_at.isoformat(),
                'ended_at': record.ended_at.isoformat() if record.ended_at else None,
                'duration_hours': record.duration_hours,
                'peak_hotness': record.peak_hotness,
                'post_count': record.post_count,
                'avg_sentiment': record.avg_sentiment,
                'predicted_next_stage': record.predicted_next_stage,
                'predicted_duration': record.predicted_duration,
                'confidence': record.confidence,
            })

        return result

    @classmethod
    def get_stage_statistics(cls, topic_id):
        """
        获取各阶段统计信息

        Args:
            topic_id: 话题ID

        Returns:
            dict: 阶段统计数据
        """
        evolution_records = OpinionEvolution.objects.filter(topic_id=topic_id)

        stage_stats = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0,
            'avg_duration': 0,
            'max_hotness': 0,
            'total_posts': 0,
        })

        for record in evolution_records:
            stage = record.stage
            stage_stats[stage]['count'] += 1
            if record.duration_hours:
                stage_stats[stage]['total_duration'] += record.duration_hours
            stage_stats[stage]['max_hotness'] = max(
                stage_stats[stage]['max_hotness'],
                record.peak_hotness
            )
            stage_stats[stage]['total_posts'] += record.post_count

        # 计算平均持续时间
        for stage, stats in stage_stats.items():
            if stats['count'] > 0:
                stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['stage_label'] = dict(OpinionEvolution.STAGE_CHOICES).get(stage, '未知')

        return dict(stage_stats)

    @classmethod
    def get_current_stage_with_prediction(cls, topic_id):
        """
        获取当前阶段及预测信息（前端API使用）

        Args:
            topic_id: 话题ID

        Returns:
            dict: 当前阶段和预测信息
        """
        # 获取当前阶段
        current_stage_info = cls.classify_evolution_stage(topic_id)

        # 获取预测
        prediction = cls.predict_next_stage(topic_id)

        # 获取阶段历史
        history = cls.get_evolution_history(topic_id, limit=10)

        # 获取阶段统计
        stage_stats = cls.get_stage_statistics(topic_id)

        return {
            'current_stage': current_stage_info,
            'prediction': prediction,
            'history': history,
            'stage_statistics': stage_stats,
        }


# 便捷函数
def get_topic_evolution_stage(topic_id):
    """获取话题演化阶段的便捷函数"""
    return OpinionEvolutionTracker.classify_evolution_stage(topic_id)


def track_evolution_transition(topic_id):
    """追踪演化转换的便捷函数"""
    return OpinionEvolutionTracker.track_stage_transitions(topic_id)


def predict_evolution_stage(topic_id):
    """预测演化阶段的便捷函数"""
    return OpinionEvolutionTracker.predict_next_stage(topic_id)
