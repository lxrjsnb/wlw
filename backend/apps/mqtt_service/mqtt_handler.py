"""
MQTT服务处理器
MQTT service handler for receiving and processing device data
"""
import json
import logging
import threading
import time
from queue import Queue, Empty
from typing import Dict, Any
from datetime import datetime, timedelta

import paho.mqtt.client as mqtt
from django.conf import settings
from django.utils import timezone

from apps.devices.models import Device, DeviceLog, SensorType
from apps.sensors.models import SensorData
from apps.alarms.models import AlarmRule, AlarmRecord

logger = logging.getLogger(__name__)


# 用于存储告警延迟检测的字典
alarm_delay_cache: Dict[str, Dict[str, Any]] = {}
alarm_cache_lock = threading.Lock()


class MQTTClient:
    """
    MQTT客户端类
    MQTT client for receiving device data
    """

    def __init__(self):
        self.client = None
        self.connected = False
        self.message_queue = Queue()
        self.worker_thread = None
        self.worker_running = False

    def on_connect(self, client, userdata, flags, rc):
        """MQTT连接回调"""
        if rc == 0:
            self.connected = True
            logger.info("MQTT client connected successfully")

            # 订阅设备数据主题
            client.subscribe("iot/+/sensor/data", qos=1)
            client.subscribe("iot/+/status", qos=1)
            logger.info("Subscribed to MQTT topics")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def on_disconnect(self, client, userdata, rc):
        """MQTT断开回调"""
        self.connected = False
        logger.warning(f"MQTT client disconnected with code {rc}")

    def on_message(self, client, userdata, msg):
        """MQTT消息接收回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')

            # 解析主题获取设备ID
            parts = topic.split('/')
            if len(parts) >= 3:
                device_id = parts[1]
                message_type = parts[2]

                # 将消息放入队列等待处理
                self.message_queue.put({
                    'device_id': device_id,
                    'message_type': message_type,
                    'topic': topic,
                    'payload': payload,
                    'timestamp': timezone.now()
                })
                logger.debug(f"MQTT message queued: {topic}")

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def start(self):
        """启动MQTT客户端"""
        if self.client and self.connected:
            logger.warning("MQTT client is already running")
            return

        # 创建MQTT客户端
        self.client = mqtt.Client(client_id="iot_backend_server")

        # 设置回调
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message

        # 配置认证
        mqtt_config = settings.MQTT_BROKER
        username = mqtt_config.get('USERNAME')
        password = mqtt_config.get('PASSWORD')

        if username and password:
            self.client.username_pw_set(username, password)

        # 连接MQTT Broker
        try:
            self.client.connect(
                mqtt_config['HOST'],
                port=mqtt_config['PORT'],
                keepalive=mqtt_config.get('KEEPALIVE', 60)
            )

            # 启动网络循环
            self.client.loop_start()

            # 启动消息处理工作线程
            self.worker_running = True
            self.worker_thread = threading.Thread(target=self.process_messages)
            self.worker_thread.daemon = True
            self.worker_thread.start()

            logger.info("MQTT client started successfully")

        except Exception as e:
            logger.error(f"Failed to start MQTT client: {e}")
            raise

    def stop(self):
        """停止MQTT客户端"""
        self.worker_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)

        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("MQTT client stopped")

    def process_messages(self):
        """消息处理工作线程"""
        logger.info("MQTT message processor started")

        while self.worker_running:
            try:
                # 从队列获取消息（超时1秒）
                message = self.message_queue.get(timeout=1)

                # 处理消息
                try:
                    self.handle_message(message)
                except Exception as e:
                    logger.error(f"Error handling message: {e}", exc_info=True)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in message processor: {e}")

        logger.info("MQTT message processor stopped")

    def handle_message(self, message: Dict[str, Any]):
        """
        处理MQTT消息

        Args:
            message: 消息字典
        """
        device_id = message['device_id']
        message_type = message['message_type']
        payload = message['payload']

        if message_type == 'sensor_data':
            self.process_sensor_data(device_id, payload)
        elif message_type == 'status':
            self.process_device_status(device_id, payload)

    def process_sensor_data(self, device_id: str, payload: str):
        """
        处理传感器数据

        Args:
            device_id: 设备ID
            payload: 数据载荷
        """
        try:
            # 解析JSON数据
            data = json.loads(payload)

            # 验证设备是否存在
            try:
                device = Device.objects.get(device_id=device_id)
            except Device.DoesNotExist:
                logger.warning(f"Device not found: {device_id}")
                return

            # 更新设备心跳时间
            device.last_heartbeat = timezone.now()
            if device.status == 'offline':
                device.status = 'online'
            device.save(update_fields=['last_heartbeat', 'status'])

            # 处理每个传感器数据
            timestamp = data.get('timestamp') or timezone.now()
            sensors = data.get('sensors', {})

            for sensor_code, value in sensors.items():
                try:
                    self.save_sensor_data(device, sensor_code, value, timestamp)
                except Exception as e:
                    logger.error(f"Error saving sensor data: {e}")

            # 通过WebSocket推送实时数据
            from consumers import send_sensor_data_sync
            send_sensor_data_sync(device_id, data)

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload from device {device_id}: {e}")
        except Exception as e:
            logger.error(f"Error processing sensor data from device {device_id}: {e}")

    def save_sensor_data(self, device: Device, sensor_code: str, value: float, timestamp):
        """
        保存传感器数据并检查告警

        Args:
            device: 设备对象
            sensor_code: 传感器代码
            value: 传感器值
            timestamp: 时间戳
        """
        # 获取传感器类型
        try:
            sensor_type = SensorType.objects.get(code=sensor_code)
        except SensorType.DoesNotExist:
            logger.warning(f"Sensor type not found: {sensor_code}")
            return

        # 创建传感器数据记录
        sensor_data = SensorData.objects.create(
            device=device,
            sensor_type=sensor_type,
            value=float(value),
            unit=sensor_type.unit,
            timestamp=timestamp,
            quality='good'
        )

        # 检查告警规则
        self.check_alarm_rules(device, sensor_type, sensor_data)

    def check_alarm_rules(self, device: Device, sensor_type, sensor_data: SensorData):
        """
        检查告警规则

        Args:
            device: 设备对象
            sensor_type: 传感器类型
            sensor_data: 传感器数据
        """
        # 获取设备启用的告警规则
        rules = AlarmRule.objects.filter(
            device=device,
            sensor_type=sensor_type,
            enabled=True
        )

        for rule in rules:
            try:
                # 检查是否满足告警条件
                if rule.check_condition(sensor_data.value):
                    self.handle_alarm_trigger(rule, sensor_data)
            except Exception as e:
                logger.error(f"Error checking alarm rule {rule.id}: {e}")

    def handle_alarm_trigger(self, rule: AlarmRule, sensor_data: SensorData):
        """
        处理告警触发

        Args:
            rule: 告警规则
            sensor_data: 传感器数据
        """
        device_id = rule.device.device_id
        key = f"{rule.id}_{device_id}"

        with alarm_cache_lock:
            current_time = time.time()

            # 检查是否在延迟窗口内
            if key in alarm_delay_cache:
                cache_entry = alarm_delay_cache[key]

                # 如果在延迟时间内，更新时间戳
                if current_time - cache_entry['start_time'] < rule.delay_minutes * 60:
                    cache_entry['last_value'] = sensor_data.value
                    cache_entry['last_time'] = current_time
                    return

            # 超过延迟时间或首次触发
            alarm_delay_cache[key] = {
                'start_time': current_time,
                'last_value': sensor_data.value,
                'last_time': current_time
            }

        # 创建告警记录
        try:
            alarm_record = AlarmRecord.objects.create(
                device=rule.device,
                alarm_rule=rule,
                sensor_type=rule.sensor_type,
                current_value=sensor_data.value,
                threshold_value=rule.threshold_max or rule.threshold_min,
                unit=sensor_data.unit,
                priority=rule.priority,
                message=f"{rule.device.name} {rule.sensor_type.name} 值为 {sensor_data.value}{sensor_data.unit}，超出阈值",
                triggered_at=sensor_data.timestamp
            )

            logger.warning(f"Alarm triggered: {alarm_record.message}")

            # 发送告警通知
            self.send_alarm_notifications(rule.device, alarm_record)

        except Exception as e:
            logger.error(f"Error creating alarm record: {e}")

    def send_alarm_notifications(self, device: Device, alarm_record: AlarmRecord):
        """
        发送告警通知

        Args:
            device: 设备对象
            alarm_record: 告警记录
        """
        # 获取设备所有者和管理员
        from django.contrib.auth import get_user_model
        User = get_user_model()

        recipients = set()
        if device.owner:
            recipients.add(device.owner)

        # 添加管理员
        admins = User.objects.filter(role='admin')
        recipients.update(admins)

        # 延迟导入序列化器避免循环导入
        from apps.alarms.serializers import AlarmRecordSerializer
        alarm_data = AlarmRecordSerializer(alarm_record).data

        # 通过WebSocket发送通知
        from consumers import send_alarm_notification_sync
        for user in recipients:
            try:
                send_alarm_notification_sync(user.id, alarm_data)
            except Exception as e:
                logger.error(f"Error sending alarm notification to user {user.id}: {e}")

        # TODO: 添加邮件和短信通知

    def process_device_status(self, device_id: str, payload: str):
        """
        处理设备状态上报

        Args:
            device_id: 设备ID
            payload: 状态载荷
        """
        try:
            data = json.loads(payload)
            status = data.get('status')

            if not status:
                return

            # 更新设备状态
            try:
                device = Device.objects.get(device_id=device_id)
                device.status = status
                device.last_heartbeat = timezone.now()
                device.save(update_fields=['status', 'last_heartbeat'])

                # 记录日志
                DeviceLog.objects.create(
                    device=device,
                    log_type='status',
                    message=f'设备状态更新为: {status}'
                )

                logger.info(f"Device {device_id} status updated to {status}")

            except Device.DoesNotExist:
                logger.warning(f"Device not found: {device_id}")

        except Exception as e:
            logger.error(f"Error processing device status: {e}")


# 全局MQTT客户端实例
mqtt_client = MQTTClient()


def start_mqtt_client():
    """启动MQTT客户端（Django管理命令调用）"""
    try:
        mqtt_client.start()
        logger.info("MQTT client started")
    except Exception as e:
        logger.error(f"Failed to start MQTT client: {e}")
        raise


def stop_mqtt_client():
    """停止MQTT客户端"""
    try:
        mqtt_client.stop()
        logger.info("MQTT client stopped")
    except Exception as e:
        logger.error(f"Error stopping MQTT client: {e}")
