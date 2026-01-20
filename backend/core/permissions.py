"""
自定义权限类
Custom permission classes
"""
from rest_framework import permissions
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    自定义权限：只有对象的所有者才能编辑
    Custom permission: Only owner can edit
    """

    def has_object_permission(self, request, view, obj):
        # 读取权限允许任何请求
        if request.method in permissions.SAFE_METHODS:
            return True

        # 写入权限只给对象的所有者
        return obj.owner == request.user


class IsAdminUser(permissions.BasePermission):
    """
    仅管理员可访问
    Only admin users can access
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'admin'


class IsDeviceOwner(permissions.BasePermission):
    """
    设备所有者权限
    Only device owner can access
    """

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user or request.user.role == 'admin'


class CanManageAlarms(permissions.BasePermission):
    """
    告警管理权限
    权限：admin、operator可以管理告警
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # 允许查看
        if request.method in permissions.SAFE_METHODS:
            return True

        # 管理员和操作员可以管理告警
        return request.user.role in ['admin', 'operator']


class CanControlDevice(permissions.BasePermission):
    """
    设备控制权限
    权限：admin、operator可以控制设备
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return (obj.owner == request.user or
                request.user.role in ['admin', 'operator'])
