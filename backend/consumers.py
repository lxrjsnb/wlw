"""
WebSocket消费者
WebSocket consumers for real-time data and alarm notifications
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class BaseWebSocketConsumer(AsyncWebsocketConsumer):
    """
    WebSocket消费者基类
    Base WebSocket consumer with common functionality
    """

    async def connect(self):
        """建立WebSocket连接"""
        # 从URL获取设备ID（可选）
        self.device_id = self.scope['url_route']['kwargs'].get('device_id')

        # 获取用户信息
        self.user = self.scope.get('user')

        # 验证用户认证
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001, reason='Unauthorized')
            return

        # 构建频道组名称
        if self.device_id:
            self.group_name = f'realtime_{self.device_id}'
        else:
            self.group_name = f'user_{self.user.id}'

        # 加入频道组
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected: {self.group_name} - {self.user.username}")

        # 发送连接成功消息
        await self.send_json({
            'type': 'connected',
            'message': 'WebSocket连接成功',
            'group': self.group_name
        })

    async def disconnect(self, close_code):
        """断开WebSocket连接"""
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )
        logger.info(f"WebSocket disconnected: {self.group_name}")

    async def receive(self, text_data):
        """接收客户端消息"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')

            if message_type == 'ping':
                await self.send_json({'type': 'pong'})

            elif message_type == 'subscribe':
                # 订阅特定设备的数据
                device_id = data.get('device_id')
                if device_id:
                    await self.channel_layer.group_add(
                        f'realtime_{device_id}',
                        self.channel_name
                    )
                    await self.send_json({
                        'type': 'subscribed',
                        'message': f'已订阅设备 {device_id} 的数据'
                    })

            elif message_type == 'unsubscribe':
                # 取消订阅
                device_id = data.get('device_id')
                if device_id:
                    await self.channel_layer.group_discard(
                        f'realtime_{device_id}',
                        self.channel_name
                    )
                    await self.send_json({
                        'type': 'unsubscribed',
                        'message': f'已取消订阅设备 {device_id} 的数据'
                    })

        except json.JSONDecodeError:
            await self.send_json({
                'type': 'error',
                'message': '无效的JSON格式'
            })
        except Exception as e:
            logger.error(f"WebSocket receive error: {e}")
            await self.send_json({
                'type': 'error',
                'message': '处理消息时出错'
            })

    async def send_json(self, data):
        """发送JSON消息"""
        await self.send(text_data=json.dumps(data, ensure_ascii=False))

    # Channel group handlers
    async def sensor_data(self, event):
        """
        处理传感器数据推送
        Handle sensor data broadcast
        """
        await self.send_json({
            'type': 'sensor_data',
            'data': event['data']
        })

    async def alarm_notification(self, event):
        """
        处理告警通知推送
        Handle alarm notification broadcast
        """
        await self.send_json({
            'type': 'alarm',
            'data': event['data']
        })

    async def device_status(self, event):
        """
        处理设备状态变更推送
        Handle device status broadcast
        """
        await self.send_json({
            'type': 'device_status',
            'data': event['data']
        })


class RealtimeDataConsumer(BaseWebSocketConsumer):
    """
    实时数据消费者
    Real-time data consumer for sensor data
    """
    pass


class AlarmConsumer(BaseWebSocketConsumer):
    """
    告警消费者
    Alarm consumer for alarm notifications
    """
    async def connect(self):
        """建立告警WebSocket连接"""
        self.user = self.scope.get('user')

        # 验证用户认证
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001, reason='Unauthorized')
            return

        # 加入用户告警组
        self.group_name = f'alarms_user_{self.user.id}'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"Alarm WebSocket connected: {self.user.username}")

        # 如果是管理员或操作员，加入全局告警组
        if self.user.role in ['admin', 'operator']:
            await self.channel_layer.group_add(
                'alarms_global',
                self.channel_name
            )


class RealtimeDataSender:
    """
    实时数据发送工具类
    Utility class for sending real-time data via WebSocket
    """
    @staticmethod
    async def send_sensor_data(device_id, data):
        """
        发送传感器数据到设备频道组
        Send sensor data to device group
        """
        from channels.layers import get_channel_layer
        layer = get_channel_layer()
        await layer.group_send(
            f'realtime_{device_id}',
            {
                'type': 'sensor_data',
                'data': data
            }
        )

    @staticmethod
    async def send_alarm_notification(user_id, alarm_data):
        """
        发送告警通知到用户频道组
        Send alarm notification to user group
        """
        from channels.layers import get_channel_layer
        layer = get_channel_layer()
        await layer.group_send(
            f'alarms_user_{user_id}',
            {
                'type': 'alarm_notification',
                'data': alarm_data
            }
        )

    @staticmethod
    async def send_global_alarm(alarm_data):
        """
        发送全局告警通知
        Send global alarm notification
        """
        from channels.layers import get_channel_layer
        layer = get_channel_layer()
        await layer.group_send(
            'alarms_global',
            {
                'type': 'alarm_notification',
                'data': alarm_data
            }
        )


def send_sensor_data_sync(device_id, data):
    """
    同步发送传感器数据
    Sync wrapper for sending sensor data
    """
    import asyncio
    from channels.layers import get_channel_layer

    layer = get_channel_layer()
    asyncio.create_task(layer.group_send(
        f'realtime_{device_id}',
        {
            'type': 'sensor_data',
            'data': data
        }
    ))


def send_alarm_notification_sync(user_id, alarm_data):
    """
    同步发送告警通知
    Sync wrapper for sending alarm notification
    """
    import asyncio
    from channels.layers import get_channel_layer

    layer = get_channel_layer()
    asyncio.create_task(layer.group_send(
        f'alarms_user_{user_id}',
        {
            'type': 'alarm_notification',
            'data': alarm_data
        }
    ))
