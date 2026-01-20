"""
Initialize sensor types and create admin user
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_system.settings')
django.setup()

from apps.devices.models import SensorType
from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
if not User.objects.filter(username='admin').exists():
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123',
        role='admin'
    )
    print("Admin user created successfully")
    print("  Username: admin")
    print("  Password: admin123")
    print("  Email: admin@example.com")
else:
    print("Admin user already exists")

# Create sensor types
sensor_types_data = [
    {
        'name': 'Temperature',
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
        'name': 'Humidity',
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
        'name': 'CO2',
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
        'name': 'Light',
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

for sensor_type_data in sensor_types_data:
    SensorType.objects.get_or_create(
        code=sensor_type_data['code'],
        defaults=sensor_type_data
    )

print("Sensor types initialized successfully")
print()
print("=" * 50)
print("Initialization complete!")
print("=" * 50)
print()
print("Start the development server:")
print("  python manage.py runserver")
print()
print("Access URLs:")
print("  API Docs: http://localhost:8000/swagger/")
print("  Admin:    http://localhost:8000/admin/")
print()
