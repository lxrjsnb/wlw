"""
预警相关异步任务
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta

from .services import AlertChecker


@shared_task(name='alerts.check_alert_rules')
def check_alert_rules():
    """
    检查所有预警规则

    定期任务，建议配置为每10分钟运行一次
    """
    try:
        checker = AlertChecker()
        result = checker.check_all_rules()
        return result
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='alerts.check_specific_rule')
def check_specific_rule(rule_id: int):
    """
    检查特定的预警规则

    Args:
        rule_id: 规则ID
    """
    try:
        from apps.alerts.models import AlertRule

        rule = AlertRule.objects.get(id=rule_id)

        if not rule.enabled:
            return {'status': 'disabled', 'rule_id': rule_id}

        checker = AlertChecker()
        is_triggered, current_value = checker._check_rule(rule)

        if is_triggered:
            checker._create_alert_record(rule, current_value)
            rule.last_triggered_at = timezone.now()
            rule.save()
            return {'status': 'triggered', 'rule_id': rule_id, 'current_value': current_value}

        return {'status': 'ok', 'rule_id': rule_id, 'current_value': current_value}

    except AlertRule.DoesNotExist:
        return {'status': 'error', 'message': f'Rule {rule_id} not found'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@shared_task(name='alerts.resolve_old_pending_alerts')
def resolve_old_pending_alerts(hours=48):
    """
    自动解决旧的待处理预警

    Args:
        hours: 多少小时前的待处理预警自动解决
    """
    try:
        from apps.alerts.models import AlertRecord

        cutoff_time = timezone.now() - timedelta(hours=hours)
        old_pending_alerts = AlertRecord.objects.filter(
            status='pending',
            triggered_at__lt=cutoff_time
        )

        count = 0
        for alert in old_pending_alerts:
            alert.status = 'resolved'
            alert.resolution_note = f'系统自动解决（超过{hours}小时未处理）'
            alert.save()
            count += 1

        return {
            'status': 'success',
            'resolved_count': count
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='alerts.cleanup_old_records')
def cleanup_old_records(days=90):
    """
    清理旧的预警记录

    Args:
        days: 保留最近几天的记录
    """
    try:
        from apps.alerts.models import AlertRecord, AlertNotificationLog

        cutoff_date = timezone.now() - timedelta(days=days)

        # 删除旧的预警记录
        deleted_alerts = AlertRecord.objects.filter(
            triggered_at__lt=cutoff_date,
            status__in=['resolved', 'ignored']
        ).delete()[0]

        # 删除旧的通知日志
        deleted_logs = AlertNotificationLog.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]

        return {
            'status': 'success',
            'deleted_alerts': deleted_alerts,
            'deleted_logs': deleted_logs
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }


@shared_task(name='alerts.send_daily_summary')
def send_daily_summary():
    """
    发送每日预警汇总

    建议每天早上运行
    """
    try:
        from apps.alerts.models import AlertRecord
        from django.db.models import Count

        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        # 获取昨天的预警统计
        yesterday_alerts = AlertRecord.objects.filter(
            triggered_at__date=yesterday
        )

        summary = {
            'date': yesterday.strftime('%Y-%m-%d'),
            'total_alerts': yesterday_alerts.count(),
            'by_status': yesterday_alerts.values('status').annotate(
                count=Count('id')
            ).order_by('-count'),
            'by_priority': yesterday_alerts.values('alert_rule__priority').annotate(
                count=Count('id')
            ).order_by('-count'),
        }

        # TODO: 发送邮件给管理员
        # from django.core.mail import send_mail
        # send_mail(
        #     subject=f'每日预警汇总 - {yesterday}',
        #     message=str(summary),
        #     from_email='noreply@example.com',
        #     recipient_list=['admin@example.com'],
        # )

        return {
            'status': 'success',
            'summary': summary
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
