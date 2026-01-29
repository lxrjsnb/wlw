"""
Celery配置 - 社交媒体舆情分析系统
"""
import os
from celery import Celery
from celery.schedules import crontab

# 设置默认Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_system.settings')

app = Celery('sentiment_analysis')

# 使用Django的设置文件配置Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有安装的app中的tasks.py
app.autodiscover_tasks()

# Celery Beat配置 - 定时任务
app.conf.beat_schedule = {
    # 每5分钟生成模拟帖子数据
    'generate-simulated-posts': {
        'task': 'posts.generate_simulated_posts',
        'schedule': 300.0,  # 5分钟
    },

    # 每10分钟检查预警规则
    'check-alert-rules': {
        'task': 'alerts.check_alert_rules',
        'schedule': 600.0,  # 10分钟
    },

    # 每小时更新帖子互动数据
    'update-post-engagement': {
        'task': 'posts.update_post_engagement',
        'schedule': 3600.0,  # 1小时
    },

    # 每天凌晨1点生成每日汇总
    'generate-daily-summary': {
        'task': 'posts.generate_daily_summary',
        'schedule': crontab(hour=1, minute=0),
    },

    # 每天凌晨2点发送每日预警汇总
    'send-daily-alert-summary': {
        'task': 'alerts.send_daily_summary',
        'schedule': crontab(hour=2, minute=0),
    },

    # 每周日凌晨3点清理旧数据
    'cleanup-old-data': {
        'task': 'posts.cleanup_old_posts',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
    },
}

# Celery配置
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30分钟超时
    task_soft_time_limit=25 * 60,  # 25分钟软超时
    worker_prefetch_multiplier=4,  # 每个worker预取4个任务
    worker_max_tasks_per_child=1000,  # 每个worker执行1000个任务后重启
)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """调试任务"""
    print(f'Request: {self.request!r}')


# 任务结果过期时间
app.conf.result_expires = 3600  # 1小时

# 任务重试配置
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1
