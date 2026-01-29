"""
WebSocket消费者 - 实时推送
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()


class RealtimePostConsumer(AsyncWebsocketConsumer):
    """实时帖子推送消费者"""

    async def connect(self):
        """处理WebSocket连接"""
        # 获取当前用户
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # 加入用户个人组（接收所有通知）
        self.group_name = f'posts_user_{self.user.id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': 'WebSocket连接成功'
        }))

    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        # 离开所有组
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """接收前端消息"""
        try:
            data = json.loads(text_data)

            # 处理订阅话题
            if data.get('type') == 'subscribe_topic':
                topic_id = data.get('topic_id')
                if topic_id:
                    await self.subscribe_to_topic(topic_id)

            # 处理取消订阅话题
            elif data.get('type') == 'unsubscribe_topic':
                topic_id = data.get('topic_id')
                if topic_id:
                    await self.unsubscribe_from_topic(topic_id)

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def subscribe_to_topic(self, topic_id):
        """订阅特定话题"""
        group_name = f'posts_topic_{topic_id}'
        await self.channel_layer.group_add(
            group_name,
            self.channel_name
        )

        await self.send(text_data=json.dumps({
            'type': 'subscribed',
            'topic_id': topic_id,
            'message': f'已订阅话题 {topic_id}'
        }))

    async def unsubscribe_from_topic(self, topic_id):
        """取消订阅话题"""
        group_name = f'posts_topic_{topic_id}'
        await self.channel_layer.group_discard(
            group_name,
            self.channel_name
        )

        await self.send(text_data=json.dumps({
            'type': 'unsubscribed',
            'topic_id': topic_id,
            'message': f'已取消订阅话题 {topic_id}'
        }))

    async def new_post(self, event):
        """推送新帖子"""
        await self.send(text_data=json.dumps({
            'type': 'new_post',
            'data': event.get('data')
        }))


class AlertNotificationConsumer(AsyncWebsocketConsumer):
    """预警通知消费者"""

    async def connect(self):
        """处理WebSocket连接"""
        # 获取当前用户
        self.user = self.scope.get('user')

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # 加入预警通知组
        self.group_name = f'alerts_user_{self.user.id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

        # 发送连接成功消息
        await self.send(text_data=json.dumps({
            'type': 'connected',
            'message': '预警通知WebSocket连接成功'
        }))

    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        # 离开预警通知组
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        """接收前端消息"""
        try:
            data = json.loads(text_data)

            # 处理订阅话题预警
            if data.get('type') == 'subscribe_topic_alerts':
                topic_id = data.get('topic_id')
                if topic_id:
                    await self.subscribe_to_topic_alerts(topic_id)

            # 处理取消订阅话题预警
            elif data.get('type') == 'unsubscribe_topic_alerts':
                topic_id = data.get('topic_id')
                if topic_id:
                    await self.unsubscribe_from_topic_alerts(topic_id)

        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    async def subscribe_to_topic_alerts(self, topic_id):
        """订阅特定话题的预警"""
        group_name = f'alerts_topic_{topic_id}'
        await self.channel_layer.group_add(
            group_name,
            self.channel_name
        )

        await self.send(text_data=json.dumps({
            'type': 'subscribed',
            'topic_id': topic_id,
            'message': f'已订阅话题 {topic_id} 的预警'
        }))

    async def unsubscribe_from_topic_alerts(self, topic_id):
        """取消订阅话题的预警"""
        group_name = f'alerts_topic_{topic_id}'
        await self.channel_layer.group_discard(
            group_name,
            self.channel_name
        )

        await self.send(text_data=json.dumps({
            'type': 'unsubscribed',
            'topic_id': topic_id,
            'message': f'已取消订阅话题 {topic_id} 的预警'
        }))

    async def alert_notification(self, event):
        """推送预警通知"""
        await self.send(text_data=json.dumps({
            'type': 'alert',
            'data': event.get('data')
        }))
