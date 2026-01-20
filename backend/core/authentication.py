"""
自定义JWT认证逻辑
Custom JWT authentication logic
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class CustomJWTAuthentication(JWTAuthentication):
    """
    自定义JWT认证类
    支持从Cookie、Header中获取Token
    """

    def get_header(self, request):
        """
        从请求中获取Authorization header
        支持从Cookie中读取Token
        """
        header = super().get_header(request)

        # 如果从Header中未获取到，尝试从Cookie中获取
        if header is None:
            token = request.COOKIES.get('access_token')
            if token:
                return f'Bearer {token}'

        return header

    def get_user(self, validated_token):
        """
        根据Token获取用户
        增加用户状态检查
        """
        try:
            user_id = validated_token[self.user_id_field]
        except KeyError:
            raise InvalidToken('Token contained no recognizable user identification')

        try:
            user = User.objects.get(**{self.user_id_field: user_id})
        except User.DoesNotExist:
            raise InvalidToken('User not found')

        # 检查用户是否被禁用
        if not user.is_active:
            raise InvalidToken('User account is disabled')

        return user

    def authenticate(self, request):
        """
        认证请求
        记录认证日志
        """
        try:
            auth = super().authenticate(request)
            if auth:
                user, token = auth
                logger.debug(f"User {user.username} authenticated successfully")
            return auth
        except TokenError as e:
            logger.warning(f"Authentication failed: {str(e)}")
            raise
