"""
预警规则检查器
"""
from datetime import timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from django.core.cache import cache

from apps.alerts.models import AlertRule, AlertRecord
from apps.posts.models import SocialPost
from apps.topics.models import Topic


class AlertChecker:
    """预警规则检查器"""

    def __init__(self):
        """初始化检查器"""
        self.notification_service = NotificationService()

    def check_all_rules(self) -> Dict:
        """
        检查所有启用的预警规则

        Returns:
            dict: {
                'total_rules': int,
                'checked_rules': int,
                'triggered_alerts': int,
                'errors': list
            }
        """
        enabled_rules = AlertRule.objects.filter(enabled=True)
        triggered_count = 0
        errors = []

        for rule in enabled_rules:
            try:
                # 检查冷却期
                if rule.is_in_cooldown():
                    continue

                # 检查规则
                is_triggered, current_value = self._check_rule(rule)

                if is_triggered:
                    # 创建预警记录
                    self._create_alert_record(rule, current_value)
                    triggered_count += 1

                    # 更新最后触发时间
                    rule.last_triggered_at = timezone.now()
                    rule.save()

            except Exception as e:
                errors.append({
                    'rule_id': rule.id,
                    'error': str(e)
                })

        return {
            'total_rules': enabled_rules.count(),
            'checked_rules': enabled_rules.count() - len(errors),
            'triggered_alerts': triggered_count,
            'errors': errors
        }

    def _check_rule(self, rule: AlertRule) -> tuple:
        """
        检查单个规则

        Returns:
            tuple: (is_triggered, current_value)
        """
        topic = rule.topic

        if rule.rule_type == 'sentiment':
            return self._check_sentiment(rule, topic)
        elif rule.rule_type == 'volume':
            return self._check_volume(rule, topic)
        elif rule.rule_type == 'influence':
            return self._check_influence(rule, topic)
        elif rule.rule_type == 'negative_ratio':
            return self._check_negative_ratio(rule, topic)
        else:
            return False, 0

    def _check_sentiment(self, rule: AlertRule, topic: Topic) -> tuple:
        """检查情感告警"""
        # 获取最近1小时的帖子
        since = timezone.now() - timedelta(hours=1)
        posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=since
        )

        if not posts.exists():
            return False, 0

        # 计算平均情感分数
        avg_sentiment = posts.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0

        # 检查条件
        is_triggered = self._evaluate_condition(
            avg_sentiment,
            rule.condition,
            rule.threshold_value,
            rule.threshold_value_max
        )

        return is_triggered, avg_sentiment

    def _check_volume(self, rule: AlertRule, topic: Topic) -> tuple:
        """检查数量告警"""
        # 获取最近1小时的帖子数
        since = timezone.now() - timedelta(hours=1)
        count = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=since
        ).count()

        # 检查条件
        is_triggered = self._evaluate_condition(
            count,
            rule.condition,
            rule.threshold_value,
            rule.threshold_value_max
        )

        return is_triggered, count

    def _check_influence(self, rule: AlertRule, topic: Topic) -> tuple:
        """检查影响力告警"""
        # 获取最近1小时的帖子
        since = timezone.now() - timedelta(hours=1)
        posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=since
        )

        if not posts.exists():
            return False, 0

        # 计算平均影响力
        avg_influence = posts.aggregate(Avg('influence_score'))['influence_score__avg'] or 0

        # 检查条件
        is_triggered = self._evaluate_condition(
            avg_influence,
            rule.condition,
            rule.threshold_value,
            rule.threshold_value_max
        )

        return is_triggered, avg_influence

    def _check_negative_ratio(self, rule: AlertRule, topic: Topic) -> tuple:
        """检查负面率告警"""
        # 获取最近1小时的帖子
        since = timezone.now() - timedelta(hours=1)
        posts = SocialPost.objects.filter(
            topic=topic,
            publish_time__gte=since
        )

        if not posts.exists():
            return False, 0

        # 计算负面比例
        total_count = posts.count()
        negative_count = posts.filter(sentiment='negative').count()
        negative_ratio = (negative_count / total_count * 100) if total_count > 0 else 0

        # 检查条件
        is_triggered = self._evaluate_condition(
            negative_ratio,
            rule.condition,
            rule.threshold_value,
            rule.threshold_value_max
        )

        return is_triggered, negative_ratio

    def _evaluate_condition(
        self,
        current_value: float,
        condition: str,
        threshold_value: float,
        threshold_value_max: Optional[float] = None
    ) -> bool:
        """评估条件"""
        if condition == 'greater_than':
            return current_value > threshold_value
        elif condition == 'less_than':
            return current_value < threshold_value
        elif condition == 'equals':
            return abs(current_value - threshold_value) < 0.001
        elif condition == 'not_equals':
            return abs(current_value - threshold_value) >= 0.001
        elif condition == 'between':
            if threshold_value_max is not None:
                return threshold_value <= current_value <= threshold_value_max
            return False
        return False

    def _create_alert_record(self, rule: AlertRule, current_value: float):
        """创建预警记录"""
        # 生成预警消息
        message = self._generate_alert_message(rule, current_value)

        # 创建记录
        record = AlertRecord.objects.create(
            topic=rule.topic,
            alert_rule=rule,
            current_value=current_value,
            threshold_value=rule.threshold_value,
            message=message,
            details={
                'rule_type': rule.rule_type,
                'condition': rule.condition,
            }
        )

        # 发送通知
        self.notification_service.send_alert_notification(record)

    def _generate_alert_message(self, rule: AlertRule, current_value: float) -> str:
        """生成预警消息"""
        topic_name = rule.topic.name
        rule_type_name = rule.get_rule_type_display()
        condition_name = rule.get_condition_display()

        message = f"【{rule.priority_display}预警】话题「{topic_name}」触发了{rule_type_name}规则\n"
        message += f"当前值: {current_value:.2f}，阈值: {rule.threshold_value}（{condition_name}）"

        return message


class AlertStatsCalculator:
    """预警统计计算器"""

    @staticmethod
    def calculate_topic_alert_stats(topic_id: int, days: int = 30) -> Dict:
        """计算话题预警统计"""
        since = timezone.now() - timedelta(days=days)
        records = AlertRecord.objects.filter(
            topic_id=topic_id,
            triggered_at__gte=since
        )

        return {
            'total_alerts': records.count(),
            'pending_alerts': records.filter(status='pending').count(),
            'resolved_alerts': records.filter(status='resolved').count(),
            'avg_response_time': AlertStatsCalculator._calculate_avg_response_time(records)
        }

    @staticmethod
    def _calculate_avg_response_time(records) -> Optional[float]:
        """计算平均响应时间（分钟）"""
        resolved_records = records.filter(
            status='resolved',
            resolved_at__isnull=False
        )

        if not resolved_records.exists():
            return None

        total_minutes = 0
        count = 0

        for record in resolved_records:
            if record.triggered_at and record.resolved_at:
                delta = record.resolved_at - record.triggered_at
                total_minutes += delta.total_seconds() / 60
                count += 1

        return total_minutes / count if count > 0 else None
