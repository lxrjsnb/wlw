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
python manage.py makemigrations devices
python manage.py makemigrations sensors
python manage.py makemigrations alarms

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

## 5. 初始化传感器类型数据

创建文件 `init_data.py`：

```python
from apps.devices.models import SensorType
from django.contrib.auth import get_user_model

User = get_user_model()

# 创建传感器类型
sensor_types = [
    {
        'name': '温度',
        'code': 'temperature',
        'unit': '°C',
        'category': 'environment',
        'icon': 'Sunny',
        'color': '#ff6b6b',
        'min_value': -40,
        'max_value': 80,
        'precision': 1,
        'sort_order': 1
    },
    {
        'name': '湿度',
        'code': 'humidity',
        'unit': '%',
        'category': 'environment',
        'icon': 'Cloudy',
        'color': '#4ecdc4',
        'min_value': 0,
        'max_value': 100,
        'precision': 1,
        'sort_order': 2
    },
    {
        'name': 'PM2.5',
        'code': 'pm25',
        'unit': 'μg/m³',
        'category': 'air_quality',
        'icon': 'WindPower',
        'color': '#95e1d3',
        'min_value': 0,
        'max_value': 500,
        'precision': 0,
        'sort_order': 3
    },
    {
        'name': 'CO2浓度',
        'code': 'co2',
        'unit': 'ppm',
        'category': 'air_quality',
        'icon': 'Cpu',
        'color': '#dda0dd',
        'min_value': 0,
        'max_value': 5000,
        'precision': 0,
        'sort_order': 4
    },
    {
        'name': '光照强度',
        'code': 'light',
        'unit': 'lux',
        'category': 'environment',
        'icon': 'Sunny',
        'color': '#feca57',
        'min_value': 0,
        'max_value': 100000,
        'precision': 0,
        'sort_order': 5
    }
]

for sensor_type_data in sensor_types:
    SensorType.objects.get_or_create(
        code=sensor_type_data['code'],
        defaults=sensor_type_data
    )

print('传感器类型初始化完成')
```

运行初始化脚本：

```bash
python init_data.py
```

## 6. 启动开发服务器

```bash
python manage.py runserver
```

服务器将在 `http://localhost:8000` 启动

## 7. 访问应用

### 后端API文档
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

### 管理后台
- 地址: http://localhost:8000/admin/
- 使用之前创建的超级用户登录

## 8. 测试API

使用curl或Postman测试登录接口：

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"admin\",\"password\":\"admin123\"}"
```

## 9. 启动前端（可选）

```bash
cd ../frontend
npm install
npm run dev
```

前端将在 `http://localhost:5173` 启动

## 常见问题

### 问题1：数据库连接失败

确保MySQL服务正在运行，并且 `backend/.env` 中的数据库配置正确。

### 问题2：迁移报错

尝试删除迁移文件重新生成：

```bash
# 删除迁移文件（保留 __init__.py）
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete

# 重新生成迁移
python manage.py makemigrations
python manage.py migrate
```

### 问题3：MySQL编码错误

确保数据库使用 utf8mb4 编码：

```sql
ALTER DATABASE wlw CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
