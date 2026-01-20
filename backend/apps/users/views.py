"""
用户模块视图
User views for authentication and user management
"""
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    UserSerializer,
    UserLoginSerializer,
    CustomTokenObtainPairSerializer,
    UserRegisterSerializer,
    ChangePasswordSerializer,
    UserLoginLogSerializer
)
from .models import UserLoginLog

User = get_user_model()


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    自定义JWT登录视图
    Custom JWT login view
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """
        处理登录请求

        Args:
            request: 请求对象

        Returns:
            Response: 包含Token和用户信息的响应
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response({
            'code': 0,
            'message': '登录成功',
            'data': serializer.validated_data
        }, status=status.HTTP_200_OK)


class UserInfoView(APIView):
    """
    获取当前用户信息
    Get current user information
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        获取当前用户信息

        Args:
            request: 请求对象

        Returns:
            Response: 用户信息
        """
        serializer = UserSerializer(request.user)
        return Response({
            'code': 0,
            'message': 'success',
            'data': serializer.data
        })


class UserRegisterView(generics.CreateAPIView):
    """
    用户注册视图
    User registration view
    """
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """
        创建新用户

        Args:
            request: 请求对象

        Returns:
            Response: 注册结果
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            'code': 0,
            'message': '注册成功',
            'data': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)


class ChangePasswordView(APIView):
    """
    修改密码视图
    Change password view
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        修改密码

        Args:
            request: 请求对象

        Returns:
            Response: 修改结果
        """
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({
            'code': 0,
            'message': '密码修改成功',
            'data': None
        })


class UserListView(generics.ListAPIView):
    """
    用户列表视图
    User list view (admin only)
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    from core.pagination import StandardPagination
    pagination_class = StandardPagination

    def get_queryset(self):
        """过滤查询结果"""
        queryset = super().get_queryset()
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        keyword = self.request.query_params.get('keyword')
        if keyword:
            queryset = queryset.filter(
                username__icontains=keyword
            ) | queryset.filter(
                email__icontains=keyword
            )
        return queryset


class UserDetailView(generics.RetrieveUpdateAPIView):
    """
    用户详情视图
    User detail view
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """普通用户只能查看自己的信息"""
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=user.id)


class UserLoginLogListView(generics.ListAPIView):
    """
    用户登录日志列表
    User login log list
    """
    serializer_class = UserLoginLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    from core.pagination import StandardPagination
    pagination_class = StandardPagination

    def get_queryset(self):
        """获取当前用户的登录日志"""
        user_id = self.kwargs.get('user_id')
        if user_id:
            # 管理员可以查看其他用户的日志
            if self.request.user.role == 'admin':
                return UserLoginLog.objects.filter(user_id=user_id)
        return UserLoginLog.objects.filter(user=self.request.user)


class LogoutView(APIView):
    """
    用户登出视图
    User logout view
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        处理登出请求
        (Token由前端删除，这里主要用于记录日志或清理资源)

        Args:
            request: 请求对象

        Returns:
            Response: 登出结果
        """
        # TODO: 如果使用Redis黑名单，可以在这里将Token加入黑名单

        return Response({
            'code': 0,
            'message': '登出成功',
            'data': None
        })
