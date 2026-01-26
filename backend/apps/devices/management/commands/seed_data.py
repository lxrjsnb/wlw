"""
Django 管理命令 - 生成种子数据
用于创建测试和演示用的丰富数据
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction

from apps.devices.models import Device, SensorType, DeviceLog
from apps.sensors.models import SensorData, SensorDataSummary
from apps.alarms.models import AlarmRule, AlarmRecord, AlarmNotification

User = get_user_model()


class Command(BaseCommand):
    help = '生成丰富的种子数据用于测试和演示'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除现有数据后再生成',
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)

        if clear:
            self.stdout.write(self.style.WARNING('正在清除现有数据...'))
            self.clear_data()

        self.stdout.write('开始生成种子数据...')
        with transaction.atomic():
            self.create_users()
            self.create_sensor_types()
            self.create_devices()
            self.create_sensor_data()
            self.create_alarm_rules()
            self.create_alarm_records()
            self.create_device_logs()

        self.stdout.write(self.style.SUCCESS('种子数据生成完成！'))

    def clear_data(self):
        """清除现有数据"""
        AlarmNotification.objects.all().delete()
        AlarmRecord.objects.all().delete()
        AlarmRule.objects.all().delete()
        SensorData.objects.all().delete()
        SensorDataSummary.objects.all().delete()
        DeviceLog.objects.all().delete()
        Device.objects.all().delete()
        SensorType.objects.all().delete()
        User.objects.exclude(username='admin').delete()

    def create_users(self):
        """创建测试用户"""
        self.stdout.write('创建用户...')

        users = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin123',
                'role': 'admin',
                'phone': '13800138001',
                'department': '技术部',
                'is_superuser': True,
                'is_staff': True,
            },
            {
                'username': 'operator1',
                'email': 'operator1@example.com',
                'password': 'operator123',
                'role': 'operator',
                'phone': '13800138002',
                'department': '运维部',
            },
            {
                'username': 'operator2',
                'email': 'operator2@example.com',
                'password': 'operator123',
                'role': 'operator',
                'phone': '13800138003',
                'department': '运维部',
            },
            {
                'username': 'viewer1',
                'email': 'viewer1@example.com',
                'password': 'viewer123',
                'role': 'viewer',
                'phone': '13800138004',
                'department': '监控部',
            },
            {
                'username': 'viewer2',
                'email': 'viewer2@example.com',
                'password': 'viewer123',
                'role': 'viewer',
                'phone': '13800138005',
                'department': '监控部',
            },
        ]

        admin_user = None
        for user_data in users:
            is_superuser = user_data.pop('is_superuser', False)
            is_staff = user_data.pop('is_staff', False)
            password = user_data.pop('password')

            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults=user_data
            )
            if created:
                user.set_password(password)
                user.is_superuser = is_superuser
                user.is_staff = is_staff
                user.save()
                self.stdout.write(f'  [OK] Created user: {user.username}')
            else:
                user.set_password(password)
                user.save()
                self.stdout.write(f'  [OK] Updated user: {user.username}')

            if user.username == 'admin':
                admin_user = user

        if not admin_user:
            raise Exception("Admin user not found!")
        self.admin_user = admin_user

    def create_sensor_types(self):
        """创建传感器类型"""
        self.stdout.write('创建传感器类型...')

        sensor_types = [
            {
                'name': '温度',
                'code': 'temperature',
                'unit': '°C',
                'category': 'environment',
                'description': '环境温度监测',
                'icon': 'Thermometer',
                'color': '#F56C6C',
                'min_value': 16.0,
                'max_value': 30.0,
                'precision': 1,
                'sort_order': 1,
            },
            {
                'name': '湿度',
                'code': 'humidity',
                'unit': '%',
                'category': 'environment',
                'description': '环境湿度监测',
                'icon': 'WaterDrop',
                'color': '#409EFF',
                'min_value': 30.0,
                'max_value': 70.0,
                'precision': 1,
                'sort_order': 2,
            },
            {
                'name': 'PM2.5',
                'code': 'pm25',
                'unit': 'μg/m³',
                'category': 'air_quality',
                'description': '细颗粒物浓度',
                'icon': 'Cloudy',
                'color': '#909399',
                'min_value': 0.0,
                'max_value': 75.0,
                'precision': 0,
                'sort_order': 3,
            },
            {
                'name': 'PM10',
                'code': 'pm10',
                'unit': 'μg/m³',
                'category': 'air_quality',
                'description': '可吸入颗粒物浓度',
                'icon': 'Cloudy',
                'color': '#606266',
                'min_value': 0.0,
                'max_value': 150.0,
                'precision': 0,
                'sort_order': 4,
            },
            {
                'name': 'CO2',
                'code': 'co2',
                'unit': 'ppm',
                'category': 'air_quality',
                'description': '二氧化碳浓度',
                'icon': 'Wind',
                'color': '#67C23A',
                'min_value': 400.0,
                'max_value': 1000.0,
                'precision': 0,
                'sort_order': 5,
            },
            {
                'name': 'TVOC',
                'code': 'tvoc',
                'unit': 'mg/m³',
                'category': 'air_quality',
                'description': '总挥发性有机物',
                'icon': 'Wind',
                'color': '#E6A23C',
                'min_value': 0.0,
                'max_value': 0.6,
                'precision': 3,
                'sort_order': 6,
            },
            {
                'name': '大气压',
                'code': 'pressure',
                'unit': 'hPa',
                'category': 'environment',
                'description': '大气压力监测',
                'icon': 'Gauge',
                'color': '#909399',
                'min_value': 980.0,
                'max_value': 1020.0,
                'precision': 1,
                'sort_order': 7,
            },
            {
                'name': '噪声',
                'code': 'noise',
                'unit': 'dB',
                'category': 'environment',
                'description': '环境噪声监测',
                'icon': 'Bell',
                'color': '#F56C6C',
                'min_value': 30.0,
                'max_value': 70.0,
                'precision': 1,
                'sort_order': 8,
            },
        ]

        self.sensor_type_map = {}
        for st_data in sensor_types:
            st, created = SensorType.objects.get_or_create(
                code=st_data['code'],
                defaults=st_data
            )
            if created:
                self.stdout.write(f'  [OK] 创建传感器类型: {st.name}')
            else:
                for key, value in st_data.items():
                    setattr(st, key, value)
                st.save()
                self.stdout.write(f'  [OK] 更新传感器类型: {st.name}')
            self.sensor_type_map[st.code] = st

    def create_devices(self):
        """创建设备"""
        self.stdout.write('创建设备...')

        locations = [
            '北京市朝阳区建国路88号',
            '北京市海淀区中关村大街1号',
            '上海市浦东新区陆家嘴环路1000号',
            '上海市徐汇区漕河泾开发区',
            '广州市天河区珠江新城花城大道',
            '深圳市南山区科技园南区',
            '杭州市滨江区江南大道',
            '成都市高新区天府大道',
            '武汉市洪山区光谷广场',
            '南京市鼓楼区新街口',
        ]

        device_templates = [
            {
                'prefix': 'ENV',
                'name': '环境监测站',
                'sensor_codes': ['temperature', 'humidity', 'pressure', 'noise'],
            },
            {
                'prefix': 'AIR',
                'name': '空气质量监测仪',
                'sensor_codes': ['pm25', 'pm10', 'co2', 'tvoc'],
            },
            {
                'prefix': 'ALL',
                'name': '综合监测设备',
                'sensor_codes': ['temperature', 'humidity', 'pm25', 'pm10', 'co2', 'tvoc', 'pressure', 'noise'],
            },
        ]

        self.devices = []
        device_id_num = 1
        for i, location in enumerate(locations):
            template = device_templates[i % len(device_templates)]

            # 提取参数到变量
            prefix_val = template['prefix']
            name_val = template['name']
            dev_id_str = "{}-{:03d}".format(prefix_val, device_id_num)
            dev_name_str = "{} #{}".format(name_val, i + 1)
            desc_str = "安装在{}的{}".format(location, name_val)

            # 创建设备
            device = Device.objects.create(
                device_id=dev_id_str,
                name=dev_name_str,
                location=location,
                description=desc_str,
                status=random.choice(['online', 'online', 'online', 'offline', 'error', 'maintenance']),
                owner=self.admin_user,
                ip_address="192.168.1.{}".format(100 + i),
                firmware_version="v{}.{}".format(random.randint(0, 3), random.randint(0, 9)),
                battery_level=random.randint(60, 100) if random.random() > 0.2 else None,
                last_heartbeat=timezone.now() - timedelta(minutes=random.randint(1, 60)),
            )

            # 添加传感器类型
            sensor_types = [self.sensor_type_map[code] for code in template['sensor_codes']]
            device.sensor_types.set(sensor_types)

            self.devices.append(device)
            device_id_num += 1
            self.stdout.write(f'  [OK] 创建设备: {device.name} ({device.device_id})')

    def create_sensor_data(self):
        """创建传感器数据"""
        self.stdout.write('创建传感器历史数据...')

        now = timezone.now()
        data_points_per_device = 1000  # 每个设备创建1000个数据点
        interval = timedelta(minutes=5)  # 每5分钟一个数据点

        total_data = 0
        for device in self.devices:
            sensor_types = list(device.sensor_types.all())

            for i in range(data_points_per_device):
                timestamp = now - (interval * (data_points_per_device - i))

                for sensor_type in sensor_types:
                    # 生成合理的传感器数值
                    value = self.generate_sensor_value(sensor_type)

                    # 根据时间添加一些趋势和随机波动
                    hour = timestamp.hour
                    if sensor_type.code == 'temperature':
                        # 温度昼夜变化
                        value += 3 * (1 if 14 <= hour <= 18 else -1 if 2 <= hour <= 6 else 0)
                    elif sensor_type.code == 'humidity':
                        # 湿度与温度相反
                        value -= 5 * (1 if 14 <= hour <= 18 else -1 if 2 <= hour <= 6 else 0)
                    elif sensor_type.code in ['pm25', 'pm10']:
                        # PM值早晚高峰时较高
                        value += 20 if (7 <= hour <= 9 or 17 <= hour <= 19) else 0

                    value = max(0, value)  # 确保非负

                    # 随机质量标识
                    quality = 'good'
                    if random.random() < 0.05:
                        quality = 'uncertain'
                    elif random.random() < 0.02:
                        quality = 'bad'

                    SensorData.objects.create(
                        device=device,
                        sensor_type=sensor_type,
                        value=round(value, sensor_type.precision),
                        unit=sensor_type.unit,
                        timestamp=timestamp,
                        quality=quality,
                    )
                    total_data += 1

            self.stdout.write(f'  [OK] 设备 {device.device_id}: {data_points_per_device * len(sensor_types)} 条数据')

        self.stdout.write(f'  总计: {total_data} 条传感器数据')

    def generate_sensor_value(self, sensor_type):
        """生成传感器数值"""
        base_ranges = {
            'temperature': (22, 26),
            'humidity': (45, 65),
            'pm25': (20, 80),
            'pm10': (40, 120),
            'co2': (400, 800),
            'tvoc': (0.1, 0.5),
            'pressure': (1000, 1015),
            'noise': (40, 65),
        }

        min_val, max_val = base_ranges.get(sensor_type.code, (0, 100))
        return random.uniform(min_val, max_val)

    def create_alarm_rules(self):
        """创建告警规则"""
        self.stdout.write('创建告警规则...')

        rules = [
            {
                'name': '温度过高告警',
                'description': '当环境温度超过30度时触发告警',
                'device': self.devices[0],
                'sensor_type': self.sensor_type_map['temperature'],
                'rule_type': 'threshold',
                'condition': 'greater_than',
                'threshold_max': 30.0,
                'priority': 'high',
                'enabled': True,
            },
            {
                'name': '温度过低告警',
                'description': '当环境温度低于18度时触发告警',
                'device': self.devices[0],
                'sensor_type': self.sensor_type_map['temperature'],
                'rule_type': 'threshold',
                'condition': 'less_than',
                'threshold_min': 18.0,
                'priority': 'medium',
                'enabled': True,
            },
            {
                'name': '湿度过高告警',
                'description': '当湿度超过75%时触发告警',
                'device': self.devices[0],
                'sensor_type': self.sensor_type_map['humidity'],
                'rule_type': 'threshold',
                'condition': 'greater_than',
                'threshold_max': 75.0,
                'priority': 'medium',
                'enabled': True,
            },
            {
                'name': 'PM2.5严重超标告警',
                'description': '当PM2.5超过150μg/m³时触发严重告警',
                'device': self.devices[1],
                'sensor_type': self.sensor_type_map['pm25'],
                'rule_type': 'threshold',
                'condition': 'greater_than',
                'threshold_max': 150.0,
                'priority': 'critical',
                'enabled': True,
                'delay_minutes': 5,
            },
            {
                'name': 'PM2.5超标告警',
                'description': '当PM2.5超过75μg/m³时触发告警',
                'device': self.devices[1],
                'sensor_type': self.sensor_type_map['pm25'],
                'rule_type': 'threshold',
                'condition': 'greater_than',
                'threshold_max': 75.0,
                'priority': 'high',
                'enabled': True,
                'delay_minutes': 10,
            },
            {
                'name': 'CO2浓度过高告警',
                'description': '当CO2浓度超过1000ppm时触发告警',
                'device': self.devices[1],
                'sensor_type': self.sensor_type_map['co2'],
                'rule_type': 'threshold',
                'condition': 'greater_than',
                'threshold_max': 1000.0,
                'priority': 'high',
                'enabled': True,
            },
            {
                'name': '噪声超标告警',
                'description': '当噪声超过70dB时触发告警',
                'device': self.devices[2],
                'sensor_type': self.sensor_type_map['noise'],
                'rule_type': 'threshold',
                'condition': 'greater_than',
                'threshold_max': 70.0,
                'priority': 'medium',
                'enabled': True,
            },
        ]

        for rule_data in rules:
            rule, created = AlarmRule.objects.get_or_create(
                name=rule_data['name'],
                device=rule_data['device'],
                sensor_type=rule_data['sensor_type'],
                defaults={
                    **rule_data,
                    'created_by': self.admin_user,
                }
            )
            if created:
                self.stdout.write(f'  [OK] 创建告警规则: {rule.name}')
            else:
                for key, value in rule_data.items():
                    setattr(rule, key, value)
                rule.save()
                self.stdout.write(f'  [OK] 更新告警规则: {rule.name}')

    def create_alarm_records(self):
        """创建告警记录"""
        self.stdout.write('创建告警记录...')

        now = timezone.now()
        alarm_statuses = ['pending', 'acknowledged', 'resolved', 'resolved', 'false_positive']
        users = list(User.objects.filter(role__in=['admin', 'operator']))

        # 为每个规则创建一些历史告警记录
        for rule in AlarmRule.objects.filter(enabled=True):
            num_records = random.randint(3, 10)

            for i in range(num_records):
                triggered_at = now - timedelta(
                    days=random.randint(1, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                status = random.choice(alarm_statuses)

                # 生成超过阈值的当前值
                if rule.condition == 'greater_than':
                    current_value = rule.threshold_max + random.uniform(1, 10)
                    threshold_value = rule.threshold_max
                elif rule.condition == 'less_than':
                    current_value = rule.threshold_min - random.uniform(1, 5)
                    threshold_value = rule.threshold_min
                else:
                    current_value = rule.threshold_max or 0
                    threshold_value = current_value

                record = AlarmRecord.objects.create(
                    device=rule.device,
                    alarm_rule=rule,
                    sensor_type=rule.sensor_type,
                    current_value=round(current_value, rule.sensor_type.precision if rule.sensor_type else 1),
                    threshold_value=round(threshold_value, rule.sensor_type.precision if rule.sensor_type else 1),
                    unit=rule.sensor_type.unit if rule.sensor_type else '',
                    status=status,
                    priority=rule.priority,
                    message=f'{rule.name}: 当前值 {round(current_value, 1)} 超过阈值 {round(threshold_value, 1)}',
                    triggered_at=triggered_at,
                )

                # 如果已确认或已解决，添加确认/解决信息
                if status in ['acknowledged', 'resolved', 'false_positive']:
                    acknowledged_at = triggered_at + timedelta(minutes=random.randint(5, 60))
                    record.acknowledged_at = acknowledged_at
                    record.acknowledged_by = random.choice(users)

                if status in ['resolved', 'false_positive']:
                    resolved_at = acknowledged_at + timedelta(hours=random.randint(1, 24))
                    record.resolved_at = resolved_at
                    record.resolved_by = random.choice(users)
                    if status == 'false_positive':
                        record.resolution_note = '误报：传感器校准后发现正常'
                    else:
                        record.resolution_note = '已处理：现场检查并调整设备参数'

                record.save()

                # 创建通知记录
                if random.random() > 0.3:  # 70%的告警有通知
                    AlarmNotification.objects.create(
                        alarm_record=record,
                        notification_type=random.choice(['websocket', 'email', 'sms']),
                        recipient=random.choice(users).email,
                        status=random.choice(['sent', 'sent', 'sent', 'failed']),
                        sent_at=triggered_at + timedelta(seconds=random.randint(1, 60)),
                    )

            self.stdout.write(f'  [OK] 规则 "{rule.name}": {num_records} 条告警记录')

    def create_device_logs(self):
        """创建设备日志"""
        self.stdout.write('创建设备日志...')

        log_types = ['status', 'control', 'error', 'info']
        log_messages = [
            ('status', '设备上线', {}),
            ('status', '设备离线', {}),
            ('status', '设备进入维护模式', {}),
            ('status', '设备维护完成，恢复正常', {}),
            ('control', '远程重启设备', {'command': 'restart'}),
            ('control', '更新设备配置', {'config': 'sample_rate=60'}),
            ('control', '校准传感器', {'sensor': 'temperature'}),
            ('error', '传感器数据异常', {'error': 'value_out_of_range'}),
            ('error', '通信超时', {'timeout': '30s'}),
            ('info', '固件更新完成', {'version': 'v2.3.5'}),
            ('info', '设备自检通过', {}),
        ]

        now = timezone.now()

        for device in self.devices:
            num_logs = random.randint(20, 50)

            for _ in range(num_logs):
                log_type, message, data = random.choice(log_messages)
                created_at = now - timedelta(
                    days=random.randint(1, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                DeviceLog.objects.create(
                    device=device,
                    log_type=log_type,
                    message=message,
                    data=data if data else None,
                    created_at=created_at,
                )

            self.stdout.write(f'  [OK] 设备 {device.device_id}: {num_logs} 条日志')
