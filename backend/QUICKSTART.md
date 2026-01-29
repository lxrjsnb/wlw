# 快速启动指南

## 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt
```

## 2. 创建数据库

在MySQL中执行：

```sql
CREATE DATABASE IF NOT EXISTS wlw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 3. 数据库迁移

```bash
# 生成迁移文件
python manage.py makemigrations users
python manage.py makemigrations topics
python manage.py makemigrations posts
python manage.py makemigrations analysis
python manage.py makemigrations alerts

# 执行迁移
python manage.py migrate
```

## 4. 创建超级用户

```bash
python manage.py createsuperuser
```

按照提示输入：
- 用户名：admin
- 邮箱：admin@example.com
- 密码：admin123

## 5. 初始化数据

创建文件 `init_data.py`：

```python
from apps.topics.models import Topic, Platform
from django.contrib.auth import get_user_model

User = get_user_model()

# 创建平台数据
platforms = [
    {
        'name': '微博',
        'code': 'weibo',
        'icon': 'ChatLineRound',
        'color': '#FF8200',
        'enabled': True
    },
    {
        'name': '知乎',
        'code': 'zhihu',
        'icon': 'ChatDotRound',
        'color': '#0084FF',
        'enabled': True
    },
    {
        'name': '抖音',
        'code': 'douyin',
        'icon': 'VideoPlay',
        'color': '#000000',
        'enabled': True
    },
]

for platform_data in platforms:
    Platform.objects.get_or_create(
        code=platform_data['code'],
        defaults=platform_data
    )

print('初始化完成！')
```

运行初始化脚本：
```bash
python manage.py shell < init_data.py
```

## 6. 启动开发服务器

```bash
# 启动Django服务
python manage.py runserver

# 启动Celery worker（新终端）
celery -A iot_system worker -l info

# 启动Celery beat（新终端，用于定时任务）
celery -A iot_system beat -l info

# 启动WebSocket服务（新终端，如果使用daphne）
daphne -b 0.0.0.0 -p 8001 iot_system.asgi:application
```

## 7. 访问系统

- 前端开发服务器：http://localhost:5173
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/swagger/
- 管理后台：http://localhost:8000/admin/

默认账号：
- 用户名：admin
- 密码：admin123

## 8. 测试API

```bash
# 获取JWT Token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 创建话题（需要替换YOUR_TOKEN）
curl -X POST http://localhost:8000/api/v1/topics/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试话题",
    "keywords": ["测试", "舆情"],
    "platforms": ["weibo", "zhihu"]
  }'
```

## 常见问题

### Redis 连接失败
确保Redis服务已启动：
```bash
# Windows
redis-server

# Linux/Mac
sudo systemctl start redis
```

### Celery 任务不执行
检查Celery worker是否正常运行，查看日志输出。

### WebSocket 连接失败
确保使用了正确的协议（ws://或wss://）和端口。
