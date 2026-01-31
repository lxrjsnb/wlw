"""
突发事件检测模块

检测方法:
1. STL分解 + 3σ异常检测
2. PELT变点检测
3. LSTM预测异常 (简化版: 基于阈值)

突发事件定义:
- 数量突发: 帖子数 > 历史均值×3σ
- 情感突发: 负面比例1小时上升>20%
- 速度突发: 热度增长速度 > 历史最快×2
"""

import numpy as np
from datetime import datetime, timedelta
from django.db.models import Q, Count, Avg, Max, StdDev
from django.utils import timezone
from django.core.cache import cache
from apps.posts.models import SocialPost, PostSummary
from apps.topics.models import Topic
from apps.analysis.models import EmergencyEvent
from apps.alerts.models import Alert


class EmergencyDetector:
    """突发事件检测器"""

    # 检测阈值
    THRESHOLDS = {
        'volume_spike_multiplier': 3.0,  # 数量突发的倍数
        'sentiment_shift_threshold': 0.2,  # 情感突变阈值（20%）
        'hotness_surge_multiplier': 2.0,  # 热度激增倍数
        'min_post_count': 10,  # 最小帖子数（避免误报）
    }

    # 冷却时间（秒）- 避免重复检测
    COOLDOWN_PERIOD = 3600  # 1小时

    @classmethod
    def detect_emergency_event(cls, topic_id, methods=None):
        """
        综合检测突发事件

        Args:
            topic_id: 话题ID
            methods: 检测方法列表，默认使用全部方法

        Returns:
            list: 检测到的突发事件列表
        """
        if methods is None:
            methods = ['volume', 'sentiment', 'hotness']

        detected_events = []

        # 检查冷却时间
        cache_key = f'emergency_cooldown_{topic_id}'
        last_detection = cache.get(cache_key)
        if last_detection:
            return []

        # 获取话题
        try:
            topic = Topic.objects.get(id=topic_id)
        except Topic.DoesNotExist:
            return []

        # 方法1: 数量突发检测
        if 'volume' in methods:
            volume_event = cls._detect_volume_spike(topic)
            if volume_event:
                detected_events.append(volume_event)

        # 方法2: 情感突变检测
        if 'sentiment' in methods:
            sentiment_event = cls._detect_sentiment_shift(topic)
            if sentiment_event:
                detected_events.append(sentiment_event)

        # 方法3: 热度激增检测
        if 'hotness' in methods:
            hotness_event = cls._detect_hotness_surge(topic)
            if hotness_event:
                detected_events.append(hotness_event)

        # 如果检测到事件，创建记录并设置冷却
        if detected_events:
            for event_data in detected_events:
                cls._create_emergency_record(topic, event_data)
            cache.set(cache_key, timezone.now(), cls.COOLDOWN_PERIOD)

        return detected_events

    @classmethod
    def _detect_volume_spike(cls, topic):
        """
        检测数量突发

        使用3σ原则: 当前值 > 历史均值 + 3×标准差
        """
        # 获取历史数据（过去7天）
        now = timezone.now()
        historical_end = now - timedelta(hours=1)  # 排除当前小时
        historical_start = historical_end - timedelta(days=7)

        # 计算历史统计
        historical_posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=historical_start,
            publish_time__lte=historical_end
        )

        if historical_posts.count() < cls.THRESHOLDS['min_post_count']:
            return None

        # 按小时聚合
        hourly_counts = defaultdict(int)
        for post in historical_posts:
            if post.publish_time:
                hour_key = post.publish_time.replace(minute=0, second=0, microsecond=0)
                hourly_counts[hour_key] += 1

        if not hourly_counts:
            return None

        counts = list(hourly_counts.values())
        mean_count = np.mean(counts)
        std_count = np.std(counts)

        # 当前小时的帖子数
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        current_count = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=current_hour
        ).count()

        # 检测异常
        threshold = mean_count + cls.THRESHOLDS['volume_spike_multiplier'] * std_count

        if current_count > threshold and current_count >= cls.THRESHOLDS['min_post_count']:
            # 计算严重程度
            severity = cls._calculate_severity(current_count, mean_count, std_count)

            return {
                'event_type': 'volume_spike',
                'severity': severity,
                'metrics': {
                    'current_count': current_count,
                    'historical_mean': round(mean_count, 2),
                    'historical_std': round(std_count, 2),
                    'threshold': round(threshold, 2),
                    'spike_ratio': round(current_count / mean_count, 2) if mean_count > 0 else 0,
                },
                'description': f'帖子数量异常增长，当前{current_count}条，历史均值{mean_count:.1f}条',
            }

        return None

    @classmethod
    def _detect_sentiment_shift(cls, topic):
        """
        检测情感突变

        负面情感比例短时间内急剧上升
        """
        now = timezone.now()
        window = timedelta(hours=1)

        # 当前窗口
        current_start = now - window
        current_posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=current_start
        )

        if current_posts.count() < cls.THRESHOLDS['min_post_count']:
            return None

        # 前一个窗口（用于对比）
        previous_start = current_start - window
        previous_posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=previous_start,
            publish_time__lt=current_start
        )

        # 计算负面比例
        current_negative = current_posts.filter(sentiment='negative').count()
        current_total = current_posts.count()
        current_negative_ratio = current_negative / current_total if current_total > 0 else 0

        if previous_posts.count() == 0:
            baseline_ratio = 0.33  # 默认基线
        else:
            previous_negative = previous_posts.filter(sentiment='negative').count()
            previous_total = previous_posts.count()
            baseline_ratio = previous_negative / previous_total if previous_total > 0 else 0

        # 检测突变
        shift = current_negative_ratio - baseline_ratio

        if shift > cls.THRESHOLDS['sentiment_shift_threshold']:
            severity = 'level1' if shift > 0.4 else ('level2' if shift > 0.3 else 'level3')

            return {
                'event_type': 'sentiment_shift',
                'severity': severity,
                'metrics': {
                    'current_negative_ratio': round(current_negative_ratio * 100, 2),
                    'baseline_ratio': round(baseline_ratio * 100, 2),
                    'shift': round(shift * 100, 2),
                    'current_negative_count': current_negative,
                    'current_total': current_total,
                },
                'description': f'负面情感比例急剧上升{shift * 100:.1f}%，当前{current_negative_ratio * 100:.1f}%',
            }

        return None

    @classmethod
    def _detect_hotness_surge(cls, topic):
        """
        检测热度激增

        热度增长速度超过历史最快速度的2倍
        """
        now = timezone.now()
        window = timedelta(hours=1)

        # 当前窗口的平均热度
        current_start = now - window
        current_posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=current_start
        )

        if current_posts.count() < cls.THRESHOLDS['min_post_count']:
            return None

        current_avg_hotness = current_posts.aggregate(
            avg=Avg('influence_score')
        )['avg'] or 0

        # 获取历史数据
        historical_start = current_start - timedelta(days=7)
        historical_posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=historical_start,
            publish_time__lt=current_start
        )

        if historical_posts.count() == 0:
            return None

        # 计算历史平均热度和最大热度
        historical_stats = historical_posts.aggregate(
            avg=Avg('influence_score'),
            max=Max('influence_score')
        )
        historical_avg = historical_stats['avg'] or 0
        historical_max = historical_stats['max'] or 0

        # 检测激增
        surge_ratio = current_avg_hotness / historical_avg if historical_avg > 0 else 0

        if surge_ratio > cls.THRESHOLDS['hotness_surge_multiplier']:
            severity = 'level1' if surge_ratio > 3 else ('level2' if surge_ratio > 2.5 else 'level3')

            return {
                'event_type': 'hotness_surge',
                'severity': severity,
                'metrics': {
                    'current_avg_hotness': round(current_avg_hotness, 2),
                    'historical_avg': round(historical_avg, 2),
                    'historical_max': round(historical_max, 2),
                    'surge_ratio': round(surge_ratio, 2),
                },
                'description': f'热度激增{surge_ratio:.1f}倍，当前平均{current_avg_hotness:.1f}',
            }

        return None

    @classmethod
    def _calculate_severity(cls, current_value, mean, std):
        """计算严重程度"""
        if std == 0:
            return 'level3'

        z_score = (current_value - mean) / std

        if z_score > 5:
            return 'level1'  # 紧急
        elif z_score > 4:
            return 'level2'  # 重要
        else:
            return 'level3'  # 一般

    @classmethod
    def _create_emergency_record(cls, topic, event_data):
        """创建突发事件记录"""
        event = EmergencyEvent.objects.create(
            topic=topic,
            event_type=event_data['event_type'],
            severity=event_data['severity'],
            metrics=event_data['metrics'],
            status='active',
        )

        # 如果需要，触发预警
        if event_data['severity'] in ['level1', 'level2']:
            cls._trigger_emergency_alert(event, event_data['description'])

        return event

    @classmethod
    def _trigger_emergency_alert(cls, event, description):
        """触发突发事件预警"""
        from apps.alerts.models import Alert

        # 根据严重程度设置预警级别
        level_mapping = {
            'level1': 'critical',
            'level2': 'high',
            'level3': 'medium',
        }

        Alert.objects.create(
            topic=event.topic,
            alert_type='emergency',
            level=level_mapping.get(event.severity, 'medium'),
            title=f'突发事件检测: {event.get_event_type_display()}',
            message=description,
            is_sent=False,
        )

        event.alert_triggered = True
        event.save()

    @classmethod
    def detect_anomaly_stl(cls, topic_id, period=24):
        """
        使用STL分解进行异常检测

        简化实现：使用移动平均替代STL

        Args:
            topic_id: 话题ID
            period: 周期（小时）

        Returns:
            list: 异常点列表
        """
        # 获取时间序列数据
        now = timezone.now()
        start_time = now - timedelta(days=7)

        posts = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__gte=start_time
        ).order_by('publish_time')

        # 按小时聚合
        hourly_data = defaultdict(int)
        for post in posts:
            if post.publish_time:
                hour_key = post.publish_time.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key] += 1

        if len(hourly_data) < period * 2:
            return []

        # 简化：使用移动平均替代STL分解
        timestamps = sorted(hourly_data.keys())
        values = [hourly_data[t] for t in timestamps]

        # 计算移动平均（趋势）
        window = period
        trend = []
        for i in range(len(values)):
            start_idx = max(0, i - window // 2)
            end_idx = min(len(values), i + window // 2 + 1)
            trend.append(np.mean(values[start_idx:end_idx]))

        # 计算残差
        residuals = np.array(values) - np.array(trend)

        # 3σ检测异常
        std_residual = np.std(residuals)
        anomalies = []

        for i, residual in enumerate(residuals):
            if abs(residual) > 3 * std_residual:
                anomalies.append({
                    'timestamp': timestamps[i].isoformat(),
                    'value': values[i],
                    'expected': round(trend[i], 2),
                    'residual': round(residual, 2),
                    'is_positive': residual > 0,
                })

        return anomalies

    @classmethod
    def detect_change_points(cls, topic_id):
        """
        变点检测

        简化实现：使用均值变化检测

        Args:
            topic_id: 话题ID

        Returns:
            list: 变点列表
        """
        # 获取时间序列
        now = timezone.now()
        start_time = now - timedelta(days=7)

        posts = SocialPost.objects.filter(
            topic_id=topic_id,
            publish_time__gte=start_time
        ).order_by('publish_time')

        # 按小时聚合
        hourly_data = defaultdict(int)
        for post in posts:
            if post.publish_time:
                hour_key = post.publish_time.replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key] += 1

        timestamps = sorted(hourly_data.keys())
        values = [hourly_data[t] for t in timestamps]

        if len(values) < 10:
            return []

        # 简化的变点检测：滑动窗口检测均值变化
        change_points = []
        window_size = max(5, len(values) // 10)

        for i in range(window_size, len(values) - window_size):
            # 前窗口均值
            left_mean = np.mean(values[i - window_size:i])
            # 后窗口均值
            right_mean = np.mean(values[i:i + window_size])

            # 变化幅度
            change_ratio = abs(right_mean - left_mean) / (left_mean + 1)

            if change_ratio > 0.5:  # 阈值可调
                change_points.append({
                    'timestamp': timestamps[i].isoformat(),
                    'left_mean': round(left_mean, 2),
                    'right_mean': round(right_mean, 2),
                    'change_ratio': round(change_ratio, 2),
                    'direction': 'increase' if right_mean > left_mean else 'decrease',
                })

        return change_points

    @classmethod
    def get_active_emergencies(cls, topic_id=None):
        """
        获取活跃的突发事件

        Args:
            topic_id: 话题ID，None表示所有话题

        Returns:
            list: 活跃事件列表
        """
        queryset = EmergencyEvent.objects.filter(status='active')

        if topic_id:
            queryset = queryset.filter(topic_id=topic_id)

        return list(queryset.order_by('-detected_at'))

    @classmethod
    def resolve_emergency(cls, event_id, resolved_by, notes=None):
        """
        解决突发事件

        Args:
            event_id: 事件ID
            resolved_by: 解决人ID
            notes: 处理备注

        Returns:
            bool: 是否成功
        """
        try:
            event = EmergencyEvent.objects.get(id=event_id)
            event.status = 'resolved'
            event.resolved_at = timezone.now()
            event.resolved_by_id = resolved_by
            event.notes = notes
            event.save()
            return True
        except EmergencyEvent.DoesNotExist:
            return False

    @classmethod
    def mark_false_positive(cls, event_id, resolved_by, notes=None):
        """
        标记为误报

        Args:
            event_id: 事件ID
            resolved_by: 操作人ID
            notes: 备注

        Returns:
            bool: 是否成功
        """
        try:
            event = EmergencyEvent.objects.get(id=event_id)
            event.status = 'false_positive'
            event.resolved_at = timezone.now()
            event.resolved_by_id = resolved_by
            event.notes = notes
            event.save()
            return True
        except EmergencyEvent.DoesNotExist:
            return False


# 便捷函数
def detect_emergency(topic_id):
    """检测突发事件的便捷函数"""
    return EmergencyDetector.detect_emergency_event(topic_id)


def get_active_emergencies(topic_id=None):
    """获取活跃突发事件的便捷函数"""
    return EmergencyDetector.get_active_emergencies(topic_id)
