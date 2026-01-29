"""
预警通知服务
"""
from typing import List
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from apps.alerts.models import AlertRecord, AlertNotificationLog

User = get_user_model()


class NotificationService:
    """预警通知服务"""

    def __init__(self):
        """初始化通知服务"""
        self.channel_layer = get_channel_layer()

    def send_alert_notification(self, alert_record: AlertRecord):
        """
        发送预警通知

        Args:
            alert_record: 预警记录对象
        """
        rule = alert_record.alert_rule

        # WebSocket通知
        if rule.notify_websocket:
            self._send_websocket_notification(alert_record)

        # 邮件通知
        if rule.notify_email:
            self._send_email_notification(alert_record)

        # 短信通知
        if rule.notify_sms:
            self._send_sms_notification(alert_record)

    def _send_websocket_notification(self, alert_record: AlertRecord):
        """发送WebSocket通知"""
        try:
            # 构建通知数据
            notification_data = {
                'type': 'alert',
                'data': {
                    'id': alert_record.id,
                    'topic': alert_record.topic.name,
                    'topic_id': alert_record.topic.id,
                    'rule_type': alert_record.alert_rule.get_rule_type_display(),
                    'priority': alert_record.alert_rule.priority,
                    'message': alert_record.message,
                    'current_value': alert_record.current_value,
                    'threshold_value': alert_record.threshold_value,
                    'triggered_at': alert_record.triggered_at.isoformat()
                }
            }

            # 向所有订阅该话题的用户组发送
            group_name = f'alerts_topic_{alert_record.topic.id}'
            async_to_sync(self.channel_layer.group_send)(
                group_name,
                {
                    'type': 'alert_notification',
                    'message': notification_data
                }
            )

            # 记录日志
            self._create_notification_log(
                alert_record,
                'websocket',
                f'group:{group_name}',
                'sent'
            )

        except Exception as e:
            self._create_notification_log(
                alert_record,
                'websocket',
                f'group:{group_name}',
                'failed',
                str(e)
            )

    def _send_email_notification(self, alert_record: AlertRecord):
        """发送邮件通知"""
        try:
            # 获取需要通知的用户
            rule = alert_record.alert_rule
            recipients = rule.notify_users.all()

            if not recipients:
                return

            # TODO: 实现邮件发送逻辑
            # 这里需要集成邮件服务（如SendGrid, SMTP等）
            # from django.core.mail import send_mail
            #
            # for user in recipients:
            #     send_mail(
            #         subject=f'【{rule.priority_display}预警】{alert_record.topic.name}',
            #         message=alert_record.message,
            #         from_email='noreply@example.com',
            #         recipient_list=[user.email],
            #     )
            #
            #     self._create_notification_log(
            #         alert_record,
            #         'email',
            #         user.email,
            #         'sent'
            #     )

            pass

        except Exception as e:
            for user in recipients:
                self._create_notification_log(
                    alert_record,
                    'email',
                    user.email,
                    'failed',
                    str(e)
                )

    def _send_sms_notification(self, alert_record: AlertRecord):
        """发送短信通知"""
        try:
            # 获取需要通知的用户
            rule = alert_record.alert_rule
            recipients = rule.notify_users.all()

            if not recipients:
                return

            # TODO: 实现短信发送逻辑
            # 这里需要集成短信服务（如阿里云短信、腾讯云短信等）
            # 示例代码：
            # for user in recipients:
            #     if hasattr(user, 'phone') and user.phone:
            #         # 调用短信服务API
            #         send_sms(user.phone, alert_record.message)
            #
            #         self._create_notification_log(
            #             alert_record,
            #             'sms',
            #             user.phone,
            #             'sent'
            #         )

            pass

        except Exception as e:
            for user in recipients:
                if hasattr(user, 'phone') and user.phone:
                    self._create_notification_log(
                        alert_record,
                        'sms',
                        user.phone,
                        'failed',
                        str(e)
                    )

    def _create_notification_log(
        self,
        alert_record: AlertRecord,
        notification_type: str,
        recipient: str,
        status: str,
        error_message: str = ''
    ):
        """创建通知日志"""
        AlertNotificationLog.objects.create(
            alert_record=alert_record,
            notification_type=notification_type,
            recipient=recipient,
            status=status,
            error_message=error_message,
            sent_at=None if status == 'pending' else timezone.now()
        )

    def send_batch_notification(self, alert_records: List[AlertRecord]):
        """批量发送通知"""
        for record in alert_records:
            self.send_alert_notification(record)
