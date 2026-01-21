"""
生成假数据命令
Generate mock data for testing and demonstration
"""
import random
from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.devices.models import Device, SensorType, DeviceLog
from apps.sensors.models import SensorData, SensorDataSummary
from apps.alarms.models import AlarmRule, AlarmRecord, AlarmNotification
from apps.users.models import UserLoginLog

User = get_user_model()


class Command(BaseCommand):
    help = '生成假数据用于测试和展示'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='生成的用户数量'
        )
        parser.add_argument(
            '--devices',
            type=int,
            default=15,
            help='生成的设备数量'
        )
        parser.add_argument(
            '--sensor-data-days',
            type=int,
            default=30,
            help='生成多少天的传感器数据'
        )
        parser.add_argument(
            '--alarms',
            type=int,
            default=20,
            help='生成的告警记录数量'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='清除所有现有数据'
        )

    def handle(self, *args, **options):
        users_count = options['users']
        devices_count = options['devices']
        sensor_data_days = options['sensor_data_days']
        alarms_count = options['alarms']
        clear_data = options['clear']

        if clear_data:
            self.stdout.write(self.style.WARNING('正在清除现有数据...'))
            self.clear_all_data()

        self.stdout.write(self.style.SUCCESS('开始生成假数据...'))

        with transaction.atomic():
            # 1. 创建传感器类型
            self.stdout.write('创建传感器类型...')
            sensor_types = self.create_sensor_types()

            # 2. 创建用户
            self.stdout.write(f'创建 {users_count} 个用户...')
            users = self.create_users(users_count)

            # 3. 创建设备
            self.stdout.write(f'创建 {devices_count} 个设备...')
            devices = self.create_devices(devices_count, users, sensor_types)

            # 4. 创建传感器数据
            self.stdout.write(f'生成 {sensor_data_days} 天的传感器数据...')
            self.create_sensor_data(devices, sensor_types, sensor_data_days)

            # 5. 创建告警规则
            self.stdout.write('创建告警规则...')
            alarm_rules = self.create_alarm_rules(devices, sensor_types, users)

            # 6. 创建告警记录
            self.stdout.write(f'创建 {alarms_count} 条告警记录...')
            self.create_alarm_records(alarms_count, devices, alarm_rules, users)

            # 7. 创建设备日志
            self.stdout.write('创建设备日志...')
            self.create_device_logs(devices)

            # 8. 创建用户登录日志
            self.stdout.write('创建用户登录日志...')
            self.create_login_logs(users)

        self.stdout.write(self.style.SUCCESS('假数据生成完成！'))
        self.print_summary(users, devices, sensor_types, alarm_rules)

    def clear_all_data(self):
        """清除所有现有数据"""
        DeviceLog.objects.all().delete()
        AlarmNotification.objects.all().delete()
        AlarmRecord.objects.all().delete()
        AlarmRule.objects.all().delete()
        SensorDataSummary.objects.all().delete()
        SensorData.objects.all().delete()
        Device.objects.all().delete()
        UserLoginLog.objects.all().delete()
        # 保留admin用户，删除其他用户
        User.objects.exclude(username='admin').delete()
        SensorType.objects.all().delete()

    def create_sensor_types(self):
        """创建传感器类型"""
        sensor_types_data = [
            {
                'name': '温度传感器',
                'code': 'temperature',
                'unit': '°C',
                'category': 'environment',
                'description': '测量环境温度',
                'icon': 'Temperature',
                'color': '#F56C6C',
                'min_value': -20,
                'max_value': 50,
                'precision': 1,
                'sort_order': 1,
            },
            {
                'name': '湿度传感器',
                'code': 'humidity',
                'unit': '%',
                'category': 'environment',
                'description': '测量空气湿度',
                'icon': 'Water',
                'color': '#409EFF',
                'min_value': 0,
                'max_value': 100,
                'precision': 1,
                'sort_order': 2,
            },
            {
                'name': 'PM2.5传感器',
                'code': 'pm25',
                'unit': 'μg/m³',
                'category': 'air_quality',
                'description': '测量PM2.5颗粒物浓度',
                'icon': 'Sunny',
                'color': '#E6A23C',
                'min_value': 0,
                'max_value': 500,
                'precision': 0,
                'sort_order': 3,
            },
            {
                'name': 'PM10传感器',
                'code': 'pm10',
                'unit': 'μg/m³',
                'category': 'air_quality',
                'description': '测量PM10颗粒物浓度',
                'icon': 'Cloudy',
                'color': '#F56C6C',
                'min_value': 0,
                'max_value': 600,
                'precision': 0,
                'sort_order': 4,
            },
            {
                'name': 'CO2传感器',
                'code': 'co2',
                'unit': 'ppm',
                'category': 'air_quality',
                'description': '测量二氧化碳浓度',
                'icon': 'WindPower',
                'color': '#67C23A',
                'min_value': 400,
                'max_value': 5000,
                'precision': 0,
                'sort_order': 5,
            },
            {
                'name': '气压传感器',
                'code': 'pressure',
                'unit': 'hPa',
                'category': 'environment',
                'description': '测量大气压力',
                'icon': 'Compass',
                'color': '#909399',
                'min_value': 800,
                'max_value': 1200,
                'precision': 1,
                'sort_order': 6,
            },
            {
                'name': '噪音传感器',
                'code': 'noise',
                'unit': 'dB',
                'category': 'environment',
                'description': '测量环境噪音',
                'icon': 'Bell',
                'color': '#909399',
                'min_value': 30,
                'max_value': 120,
                'precision': 1,
                'sort_order': 7,
            },
            {
                'name': '光照传感器',
                'code': 'light',
                'unit': 'lux',
                'category': 'environment',
                'description': '测量光照强度',
                'icon': 'Sunny',
                'color': '#E6A23C',
                'min_value': 0,
                'max_value': 100000,
                'precision': 0,
                'sort_order': 8,
            },
            {
                'name': 'TVOC传感器',
                'code': 'tvoc',
                'unit': 'ppb',
                'category': 'air_quality',
                'description': '测量总挥发性有机化合物',
                'icon': 'Warning',
                'color': '#F56C6C',
                'min_value': 0,
                'max_value': 1000,
                'precision': 0,
                'sort_order': 9,
            },
            {
                'name': '甲醛传感器',
                'code': 'hcho',
                'unit': 'mg/m³',
                'category': 'air_quality',
                'description': '测量甲醛浓度',
                'icon': 'Warning',
                'color': '#E6A23C',
                'min_value': 0,
                'max_value': 0.5,
                'precision': 3,
                'sort_order': 10,
            },
        ]

        sensor_types = []
        for data in sensor_types_data:
            st, _ = SensorType.objects.get_or_create(code=data['code'], defaults=data)
            sensor_types.append(st)

        return sensor_types

    def create_users(self, count):
        """创建用户"""
        users = []

        # 创建默认管理员
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'role': 'admin',
                'phone': '13800000001',
                'department': '技术部',
                'first_name': '管理员',
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        users.append(admin_user)

        # 创建操作员
        for i in range(max(1, count // 4)):
            username = f'operator{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'role': 'operator',
                    'phone': f'1380001{i+1:04d}',
                    'department': random.choice(['运维部', '监控中心', '技术部']),
                    'first_name': f'操作员{i+1}',
                }
            )
            if created:
                user.set_password('operator123')
                user.save()
            users.append(user)

        # 创建查看者
        viewer_count = count - len(users)
        for i in range(viewer_count):
            username = f'viewer{i+1}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.com',
                    'role': 'viewer',
                    'phone': f'1380002{i+1:04d}',
                    'department': random.choice(['管理部', '质检部', '综合部', '客服部']),
                    'first_name': f'查看者{i+1}',
                }
            )
            if created:
                user.set_password('viewer123')
                user.save()
            users.append(user)

        return users

    def create_devices(self, count, users, sensor_types):
        """创建设备"""
        devices = []
        locations = [
            '北京市朝阳区CBD写字楼A栋',
            '上海市浦东新区陆家嘴金融中心',
            '广州市天河区珠江新城',
            '深圳市南山区科技园',
            '杭州市滨江区物联网产业园',
            '成都市高新区天府软件园',
            '武汉市东湖高新区光谷',
            '南京市江宁区软件园',
            '西安市雁塔区高新区',
            '天津市滨海新区开发区',
            '重庆市渝北区照母山',
            '苏州市工业园区',
            '长沙市岳麓区高新区',
            '青岛市市南区软件园',
            '大连市沙河口区星海湾',
        ]

        device_names = [
            '环境监测站-{}',
            '空气质量传感器-{}',
            '温湿度采集器-{}',
            '综合监测终端-{}',
            '工业物联网网关-{}',
        ]

        statuses = ['online', 'offline', 'error', 'maintenance']

        for i in range(count):
            location = locations[i % len(locations)]
            name = device_names[i % len(device_names)].format(i+1)

            device = Device.objects.create(
                device_id=f'DEV{10000 + i}',
                name=name,
                location=location,
                description=f'安装于{location}的{name}',
                status=random.choices(
                    statuses,
                    weights=[0.6, 0.2, 0.1, 0.1],
                    k=1
                )[0],
                owner=random.choice(users),
                ip_address=f'192.168.{random.randint(1,255)}.{random.randint(1,255)}',
                firmware_version=f'{random.randint(1,3)}.{random.randint(0,9)}.{random.randint(0,99)}',
                battery_level=random.randint(20, 100) if random.random() > 0.7 else None,
                last_heartbeat=timezone.now() - timedelta(minutes=random.randint(0, 60)),
                is_active=True,
            )

            # 为设备分配传感器类型（每个设备随机3-6个传感器）
            device_sensor_types = random.sample(
                sensor_types,
                random.randint(3, min(6, len(sensor_types)))
            )
            device.sensor_types.set(device_sensor_types)

            devices.append(device)

        return devices

    def create_sensor_data(self, devices, sensor_types, days):
        """创建传感器数据"""
        # 为每个设备生成过去N天的数据
        now = timezone.now()
        start_time = now - timedelta(days=days)

        total_count = 0
        batch_size = 1000
        sensor_data_list = []

        for device in devices:
            # 只为设备支持的传感器类型生成数据
            device_sensor_types = device.sensor_types.all()

            # 生成每小时一条数据
            current_time = start_time
            while current_time <= now:
                for sensor_type in device_sensor_types:
                    # 生成合理的随机值
                    value = self.generate_sensor_value(sensor_type)

                    sensor_data = SensorData(
                        device=device,
                        sensor_type=sensor_type,
                        value=value,
                        unit=sensor_type.unit,
                        timestamp=current_time,
                        quality=random.choices(
                            ['good', 'uncertain', 'bad'],
                            weights=[0.95, 0.04, 0.01],
                            k=1
                        )[0],
                    )
                    sensor_data_list.append(sensor_data)

                    if len(sensor_data_list) >= batch_size:
                        SensorData.objects.bulk_create(sensor_data_list)
                        total_count += len(sensor_data_list)
                        sensor_data_list = []
                        self.stdout.write(f'已生成 {total_count} 条传感器数据...')

                current_time += timedelta(hours=1)

        # 创建剩余的数据
        if sensor_data_list:
            SensorData.objects.bulk_create(sensor_data_list)
            total_count += len(sensor_data_list)

        self.stdout.write(f'共生成 {total_count} 条传感器数据')

    def generate_sensor_value(self, sensor_type):
        """根据传感器类型生成合理的随机值"""
        code = sensor_type.code

        if code == 'temperature':
            # 温度：-10到40度
            return round(random.uniform(-10, 40), 1)
        elif code == 'humidity':
            # 湿度：30%到90%
            return round(random.uniform(30, 90), 1)
        elif code == 'pm25':
            # PM2.5：0到500，通常在20-150之间
            base = random.uniform(20, 150)
            if random.random() < 0.1:  # 10%概率出现污染
                base = random.uniform(150, 500)
            return round(base)
        elif code == 'pm10':
            # PM10：0到600
            base = random.uniform(30, 200)
            if random.random() < 0.1:
                base = random.uniform(200, 600)
            return round(base)
        elif code == 'co2':
            # CO2：400到5000，通常在400-1000之间
            base = random.uniform(400, 1000)
            if random.random() < 0.15:
                base = random.uniform(1000, 5000)
            return round(base)
        elif code == 'pressure':
            # 气压：980到1040
            return round(random.uniform(980, 1040), 1)
        elif code == 'noise':
            # 噪音：30到90
            base = random.uniform(40, 70)
            if random.random() < 0.1:
                base = random.uniform(70, 90)
            return round(base, 1)
        elif code == 'light':
            # 光照：0到50000
            return round(random.uniform(0, 50000))
        elif code == 'tvoc':
            # TVOC：0到500
            base = random.uniform(0, 200)
            if random.random() < 0.1:
                base = random.uniform(200, 500)
            return round(base)
        elif code == 'hcho':
            # 甲醛：0到0.2
            base = random.uniform(0, 0.08)
            if random.random() < 0.08:
                base = random.uniform(0.08, 0.2)
            return round(base, 3)

        return round(random.uniform(0, 100), 1)

    def create_alarm_rules(self, devices, sensor_types, users):
        """创建告警规则"""
        rules = []

        # 为在线设备创建告警规则
        online_devices = [d for d in devices if d.status == 'online']

        for device in online_devices[:5]:  # 为前5个在线设备创建规则
            device_sensor_types = device.sensor_types.all()

            # 为每个设备创建2-3个告警规则
            for sensor_type in device_sensor_types[:3]:
                conditions = ['greater_than', 'less_than']
                rule = AlarmRule.objects.create(
                    name=f'{device.name}-{sensor_type.name}告警',
                    description=f'{sensor_type.name}超出正常范围时触发告警',
                    device=device,
                    sensor_type=sensor_type,
                    rule_type='threshold',
                    condition=random.choice(conditions),
                    threshold_min=sensor_type.min_value,
                    threshold_max=sensor_type.max_value,
                    priority=random.choice(['low', 'medium', 'high', 'critical']),
                    enabled=True,
                    notification_enabled=True,
                    delay_minutes=random.randint(0, 5),
                    recovery_enabled=True,
                    created_by=random.choice(users),
                )
                rules.append(rule)

        return rules

    def create_alarm_records(self, count, devices, alarm_rules, users):
        """创建告警记录"""
        records = []

        if not alarm_rules:
            self.stdout.write('没有告警规则，跳过创建告警记录')
            return records

        for i in range(count):
            alarm_rule = random.choice(alarm_rules)
            device = alarm_rule.device
            sensor_type = alarm_rule.sensor_type

            # 生成告警时间（过去30天内）
            triggered_at = timezone.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            # 随机状态
            status = random.choices(
                ['pending', 'acknowledged', 'resolved', 'false_positive'],
                weights=[0.3, 0.3, 0.3, 0.1],
                k=1
            )[0]

            record = AlarmRecord.objects.create(
                device=device,
                alarm_rule=alarm_rule,
                sensor_type=sensor_type,
                current_value=self.generate_alarm_value(sensor_type, alarm_rule),
                threshold_value=alarm_rule.threshold_max or alarm_rule.threshold_min,
                unit=sensor_type.unit,
                status=status,
                priority=alarm_rule.priority,
                message=f'{sensor_type.name}数值超过阈值',
                triggered_at=triggered_at,
            )

            # 如果已确认或已解决，设置相应时间和人员
            if status in ['acknowledged', 'resolved', 'false_positive']:
                acknowledged_at = triggered_at + timedelta(minutes=random.randint(1, 60))
                record.acknowledged_at = acknowledged_at
                record.acknowledged_by = random.choice(users)

                if status == 'resolved':
                    resolved_at = acknowledged_at + timedelta(minutes=random.randint(10, 120))
                    record.resolved_at = resolved_at
                    record.resolved_by = random.choice(users)
                    record.resolution_note = '问题已处理，设备恢复正常'
                elif status == 'false_positive':
                    record.resolved_at = acknowledged_at + timedelta(minutes=random.randint(5, 30))
                    record.resolved_by = random.choice(users)
                    record.resolution_note = '误报，无需处理'

            record.save()
            records.append(record)

            # 随机创建通知记录
            if random.random() > 0.3:
                self.create_alarm_notification(record)

        return records

    def generate_alarm_value(self, sensor_type, alarm_rule):
        """生成触发告警的数值"""
        if alarm_rule.condition == 'greater_than':
            # 大于阈值，生成稍大于阈值的值
            threshold = alarm_rule.threshold_max
            return round(threshold + random.uniform(1, 20), sensor_type.precision)
        elif alarm_rule.condition == 'less_than':
            # 小于阈值，生成稍小于阈值的值
            threshold = alarm_rule.threshold_min
            return round(threshold - random.uniform(1, 20), sensor_type.precision)
        else:
            return self.generate_sensor_value(sensor_type)

    def create_alarm_notification(self, alarm_record):
        """创建告警通知记录"""
        recipients = ['admin@example.com', '13800000001']

        for recipient in recipients:
            AlarmNotification.objects.create(
                alarm_record=alarm_record,
                notification_type=random.choice(['websocket', 'email', 'sms']),
                recipient=recipient,
                status='sent' if random.random() > 0.1 else 'failed',
                sent_at=alarm_record.triggered_at + timedelta(seconds=random.randint(1, 60)),
            )

    def create_device_logs(self, devices):
        """创建设备日志"""
        log_types = ['status', 'control', 'error', 'info']
        messages = [
            '设备启动成功',
            '连接到服务器',
            '传感器数据上报完成',
            '心跳包发送成功',
            '固件升级中',
            '配置更新完成',
            '重启设备',
            '传感器校准完成',
            '电量低警告',
            '网络连接异常',
        ]

        for device in devices:
            # 为每个设备创建5-15条日志
            log_count = random.randint(5, 15)

            for _ in range(log_count):
                DeviceLog.objects.create(
                    device=device,
                    log_type=random.choice(log_types),
                    message=random.choice(messages),
                    created_at=timezone.now() - timedelta(
                        days=random.randint(0, 7),
                        hours=random.randint(0, 23),
                        minutes=random.randint(0, 59)
                    )
                )

    def create_login_logs(self, users):
        """创建用户登录日志"""
        for user in users:
            # 为每个用户创建3-10条登录日志
            log_count = random.randint(3, 10)

            for i in range(log_count):
                login_time = timezone.now() - timedelta(
                    days=random.randint(0, 30),
                    hours=random.randint(0, 23),
                    minutes=random.randint(0, 59)
                )

                UserLoginLog.objects.create(
                    user=user,
                    login_ip=f'{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                    login_time=login_time,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    login_status=random.choices(['success', 'failed'], weights=[0.9, 0.1], k=1)[0],
                )

    def print_summary(self, users, devices, sensor_types, alarm_rules):
        """打印数据统计摘要"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write('数据统计摘要:')
        self.stdout.write('='*50)
        self.stdout.write(f'用户数量: {User.objects.count()}')
        self.stdout.write(f'设备数量: {Device.objects.count()}')
        self.stdout.write(f'传感器类型: {SensorType.objects.count()}')
        self.stdout.write(f'传感器数据: {SensorData.objects.count()}')
        self.stdout.write(f'告警规则: {AlarmRule.objects.count()}')
        self.stdout.write(f'告警记录: {AlarmRecord.objects.count()}')
        self.stdout.write(f'设备日志: {DeviceLog.objects.count()}')
        self.stdout.write(f'登录日志: {UserLoginLog.objects.count()}')
        self.stdout.write('='*50)
        self.stdout.write('\n默认登录账号:')
        self.stdout.write('  管理员: admin / admin123')
        self.stdout.write('  操作员: operator1 / operator123')
        self.stdout.write('  查看者: viewer1 / viewer123')
        self.stdout.write('='*50)
