"""
Django管理命令：启动MQTT服务
Django management command to start MQTT service
"""
from django.core.management.base import BaseCommand
from apps.mqtt_service.mqtt_handler import start_mqtt_client, stop_mqtt_client
import signal
import sys


class Command(BaseCommand):
    help = 'Start MQTT service for receiving device data'

    def handle(self, *args, **options):
        """处理命令"""
        self.stdout.write(self.style.SUCCESS('Starting MQTT service...'))

        # 注册信号处理
        def signal_handler(signum, frame):
            self.stdout.write('\nStopping MQTT service...')
            stop_mqtt_client()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            # 启动MQTT客户端
            start_mqtt_client()

            # 保持运行
            self.stdout.write(self.style.SUCCESS('MQTT service is running. Press Ctrl+C to stop.'))

            # 主循环
            while True:
                import time
                time.sleep(1)

        except KeyboardInterrupt:
            self.stdout.write('\nShutting down MQTT service...')
            stop_mqtt_client()
            self.stdout.write(self.style.SUCCESS('MQTT service stopped'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            stop_mqtt_client()
            sys.exit(1)
