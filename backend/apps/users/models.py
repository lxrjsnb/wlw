"""
用户模型
User model for authentication and authorization
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    用户模型
    继承Django的AbstractUser，扩展角色和额外字段
    """
    # 用户角色选择
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('operator', '操作员'),
        ('viewer', '查看者'),
    ]

    # 扩展字段
    role = models.CharField(
        verbose_name='角色',
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer'
    )
    phone = models.CharField(
        verbose_name='手机号',
        max_length=11,
        blank=True,
        null=True
    )
    avatar = models.CharField(
        verbose_name='头像URL',
        max_length=255,
        blank=True,
        null=True
    )
    last_login_ip = models.GenericIPAddressField(
        verbose_name='最后登录IP',
        blank=True,
        null=True
    )
    department = models.CharField(
        verbose_name='部门',
        max_length=50,
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        """是否为管理员"""
        return self.role == 'admin'

    @property
    def is_operator(self):
        """是否为操作员"""
        return self.role in ['admin', 'operator']


class UserLoginLog(models.Model):
    """
    用户登录日志
    """
    user = models.ForeignKey(
        User,
        verbose_name='用户',
        on_delete=models.CASCADE,
        related_name='login_logs'
    )
    login_ip = models.GenericIPAddressField(
        verbose_name='登录IP'
    )
    login_time = models.DateTimeField(
        verbose_name='登录时间',
        auto_now_add=True
    )
    user_agent = models.CharField(
        verbose_name='User Agent',
        max_length=255,
        blank=True
    )
    login_status = models.CharField(
        verbose_name='登录状态',
        max_length=20,
        choices=[
            ('success', '成功'),
            ('failed', '失败'),
        ],
        default='success'
    )

    class Meta:
        db_table = 'user_login_logs'
        verbose_name = '登录日志'
        verbose_name_plural = '登录日志'
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.login_time}"
