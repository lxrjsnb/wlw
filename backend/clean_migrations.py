"""
清理数据库迁移表并重新初始化
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iot_system.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    # 删除所有表（除了迁移记录表）
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    # 获取所有表名
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        # 保留迁移相关表
        if table_name not in ['django_migrations']:
            print(f"删除表: {table_name}")
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    # 清空迁移记录
    cursor.execute("DELETE FROM django_migrations WHERE app IN ('admin', 'auth', 'contenttypes', 'sessions')")

print("数据库清理完成！现在运行迁移命令：")
print("python manage.py migrate")
