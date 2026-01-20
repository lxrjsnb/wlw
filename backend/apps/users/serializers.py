"""
用户模块序列化器
User serializers for authentication and user management
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.settings import api_settings
from .models import UserLoginLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    User serializer for basic user information
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'role',
                  'avatar', 'department', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserLoginSerializer(serializers.Serializer):
    """
    用户登录序列化器
    Login serializer with additional fields
    """
    username = serializers.CharField(
        max_length=150,
        error_messages={'required': '用户名不能为空'}
    )
    password = serializers.CharField(
        write_only=True,
        error_messages={'required': '密码不能为空'}
    )
    login_ip = serializers.IPAddressField(required=False, write_only=True)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    自定义JWT Token获取序列化器
    Custom JWT token serializer with additional user data
    """
    @classmethod
    def get_token(cls, user):
        """
        生成Token，添加自定义信息

        Args:
            user: 用户对象

        Returns:
            Token: 包含自定义信息的Token
        """
        token = super().get_token(user)

        # 添加自定义信息到Token
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        token['is_admin'] = user.is_admin

        return token

    def validate(self, attrs):
        """
        验证登录信息并返回Token

        Args:
            attrs: 输入属性

        Returns:
            dict: 包含Token和用户信息的字典
        """
        data = super().validate(attrs)

        # 获取客户端IP
        request = self.context.get('request')
        client_ip = self.get_client_ip(request)

        # 更新用户最后登录IP
        self.user.last_login_ip = client_ip
        self.user.save(update_fields=['last_login_ip'])

        # 记录登录日志
        try:
            UserLoginLog.objects.create(
                user=self.user,
                login_ip=client_ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                login_status='success'
            )
        except Exception as e:
            # 记录日志失败不影响登录
            pass

        # 添加用户信息到响应
        data.update({
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email,
                'role': self.user.role,
                'avatar': self.user.avatar.url if self.user.avatar else None,
            }
        })

        return data

    @staticmethod
    def get_client_ip(request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserRegisterSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    User registration serializer with password validation
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        error_messages={'required': '密码不能为空'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={'required': '确认密码不能为空'}
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password_confirm',
                  'phone', 'role', 'department']
        extra_kwargs = {
            'email': {'required': True, 'error_messages': {'required': '邮箱不能为空'}},
            'username': {'required': True, 'error_messages': {'required': '用户名不能为空'}},
        }

    def validate(self, attrs):
        """
        验证密码确认是否一致

        Args:
            attrs: 输入属性

        Returns:
            dict: 验证后的属性

        Raises:
            ValidationError: 密码不一致时
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': '两次密码输入不一致'
            })
        return attrs

    def create(self, validated_data):
        """
        创建用户

        Args:
            validated_data: 验证后的数据

        Returns:
            User: 创建的用户对象
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    修改密码序列化器
    Change password serializer with validation
    """
    old_password = serializers.CharField(
        required=True,
        error_messages={'required': '旧密码不能为空'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        error_messages={'required': '新密码不能为空'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        error_messages={'required': '确认新密码不能为空'}
    )

    def validate(self, attrs):
        """验证密码"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': '两次密码输入不一致'
            })
        return attrs

    def validate_old_password(self, value):
        """
        验证旧密码是否正确

        Args:
            value: 旧密码

        Returns:
            str: 旧密码

        Raises:
            ValidationError: 密码错误时
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('旧密码错误')
        return value


class UserLoginLogSerializer(serializers.ModelSerializer):
    """
    用户登录日志序列化器
    """
    class Meta:
        model = UserLoginLog
        fields = ['id', 'login_ip', 'login_time', 'user_agent', 'login_status']
        read_only_fields = ['id', 'login_time']
