"""
初始化数据脚本
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_system.settings')
django.setup()

from apps.topics.models import Platform, Topic
from apps.users.models import User


def create_platforms():
    """创建社交媒体平台"""
    platforms_data = [
        {'name': '微博', 'code': 'weibo', 'icon': 'weibo', 'color': '#ff8200', 'sort_order': 1},
        {'name': '微信', 'code': 'wechat', 'icon': 'wechat', 'color': '#07c160', 'sort_order': 2},
        {'name': '抖音', 'code': 'douyin', 'icon': 'douyin', 'color': '#000000', 'sort_order': 3},
        {'name': '知乎', 'code': 'zhihu', 'icon': 'zhihu', 'color': '#0084ff', 'sort_order': 4},
        {'name': 'B站', 'code': 'bilibili', 'icon': 'bilibili', 'color': '#00aeec', 'sort_order': 5},
        {'name': '小红书', 'code': 'xiaohongshu', 'icon': 'xiaohongshu', 'color': '#ff2442', 'sort_order': 6},
        {'name': '今日头条', 'code': 'toutiao', 'icon': 'toutiao', 'color': '#f85959', 'sort_order': 7},
    ]

    created_count = 0
    for data in platforms_data:
        platform, created = Platform.objects.get_or_create(
            code=data['code'],
            defaults=data
        )
        if created:
            print(f"✓ 创建平台: {platform.name}")
            created_count += 1
        else:
            print(f"⊙ 平台已存在: {platform.name}")

    return created_count


def create_sample_topics(user):
    """创建示例话题"""
    topics_data = [
        {
            'name': '人工智能发展',
            'description': '关注人工智能领域的最新发展动态、技术突破和应用案例',
            'keywords': ['人工智能', 'AI', '机器学习', '深度学习', 'GPT', '大模型'],
            'priority': 'high',
            'platform_codes': ['weibo', 'zhihu', 'bilibili']
        },
        {
            'name': '新能源汽车',
            'description': '监控新能源汽车行业动态、政策变化和用户反馈',
            'keywords': ['新能源汽车', '电动车', '充电桩', '电池', '特斯拉', '比亚迪'],
            'priority': 'high',
            'platform_codes': ['weibo', 'douyin', 'xiaohongshu']
        },
        {
            'name': '教育改革',
            'description': '关注教育政策改革、在线教育发展等话题',
            'keywords': ['教育', '双减', '在线教育', '高考', '留学', '职业教育'],
            'priority': 'medium',
            'platform_codes': ['weibo', 'wechat', 'zhihu']
        },
        {
            'name': '医疗健康',
            'description': '医疗健康领域的政策动态和公众讨论',
            'keywords': ['医疗', '健康', '医保', '疫苗', '互联网医疗'],
            'priority': 'medium',
            'platform_codes': ['weibo', 'wechat', 'zhihu']
        },
        {
            'name': '环保政策',
            'description': '环境保护政策及公众对环保话题的关注度',
            'keywords': ['环保', '碳中和', '垃圾分类', '新能源', '可持续发展'],
            'priority': 'medium',
            'platform_codes': ['weibo', 'xiaohongshu', 'zhihu']
        },
    ]

    created_count = 0
    for data in topics_data:
        platform_codes = data.pop('platform_codes', [])

        # 检查话题是否已存在
        existing_topic = Topic.objects.filter(name=data['name']).first()
        if existing_topic:
            print(f"⊙ 话题已存在: {data['name']}")
            continue

        # 创建话题
        topic = Topic.objects.create(
            **data,
            owner=user,
            status='active'
        )

        # 关联平台
        for code in platform_codes:
            try:
                platform = Platform.objects.get(code=code)
                topic.platforms.add(platform)
            except Platform.DoesNotExist:
                print(f"⚠ 平台不存在: {code}")

        print(f"✓ 创建话题: {topic.name}")
        created_count += 1

    return created_count


def create_alert_rules(user, topics):
    """创建示例预警规则"""
    from apps.alerts.models import AlertRule

    rules_data = [
        {
            'topic': topics[0],  # 人工智能发展
            'rule_type': 'sentiment',
            'condition': 'less_than',
            'threshold_value': -0.3,
            'priority': 'high',
            'description': '当平均情感分数低于-0.3时触发告警（负面情绪过高）'
        },
        {
            'topic': topics[0],
            'rule_type': 'volume',
            'condition': 'greater_than',
            'threshold_value': 500,
            'priority': 'medium',
            'description': '当1小时内帖子数超过500时触发告警（话题热度异常）'
        },
        {
            'topic': topics[1],  # 新能源汽车
            'rule_type': 'negative_ratio',
            'condition': 'greater_than',
            'threshold_value': 30,
            'priority': 'high',
            'description': '当负面帖子占比超过30%时触发告警'
        },
        {
            'topic': topics[2],  # 教育改革
            'rule_type': 'influence',
            'condition': 'greater_than',
            'threshold_value': 5000,
            'priority': 'medium',
            'description': '当平均影响力分数超过5000时触发告警'
        },
    ]

    created_count = 0
    for data in rules_data:
        # 检查规则是否已存在（同一话题的同一规则类型）
        existing_rule = AlertRule.objects.filter(
            topic=data['topic'],
            rule_type=data['rule_type']
        ).first()

        if existing_rule:
            print(f"⊙ 预警规则已存在: {data['topic'].name} - {data['rule_type']}")
            continue

        rule = AlertRule.objects.create(**data)
        rule.notify_users.add(user)
        print(f"✓ 创建预警规则: {rule.topic.name} - {rule.get_rule_type_display()}")
        created_count += 1

    return created_count


def main():
    """主函数"""
    print("=" * 60)
    print("社交媒体舆情分析系统 - 初始化数据")
    print("Social Media Sentiment Analysis System - Data Initialization")
    print("=" * 60)
    print()

    # 1. 创建平台
    print("[1/4] 创建社交媒体平台...")
    platforms_count = create_platforms()
    print(f"✓ 平台创建完成: 新增 {platforms_count} 个平台")
    print()

    # 2. 创建管理员用户
    print("[2/4] 创建管理员用户...")
    admin_user = User.objects.filter(username='admin').first()
    if not admin_user:
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123'
        )
        print("✓ 创建管理员用户: admin / admin123")
    else:
        print("⊙ 管理员用户已存在: admin")
    print()

    # 3. 创建示例话题
    print("[3/4] 创建示例话题...")
    topics_count = create_sample_topics(admin_user)
    print(f"✓ 话题创建完成: 新增 {topics_count} 个话题")
    print()

    # 4. 创建预警规则
    print("[4/4] 创建预警规则...")
    topics = list(Topic.objects.all()[:5])  # 获取前5个话题
    if topics:
        rules_count = create_alert_rules(admin_user, topics)
        print(f"✓ 预警规则创建完成: 新增 {rules_count} 条规则")
    else:
        print("⚠ 没有可用的话题，跳过预警规则创建")
    print()

    print("=" * 60)
    print("✓ 数据初始化完成！")
    print()
    print("登录信息:")
    print("  用户名: admin")
    print("  密码: admin123")
    print()
    print("接下来可以:")
    print("  1. 运行 'python manage.py runserver' 启动后端服务")
    print("  2. 运行 'celery -A iot_system worker -l info' 启动Celery Worker")
    print("  3. 运行 'celery -A iot_system beat -l info' 启动Celery Beat")
    print("  4. 访问 http://localhost:8000/swagger/ 查看API文档")
    print("=" * 60)


if __name__ == '__main__':
    main()
