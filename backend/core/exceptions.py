"""
自定义异常处理
Custom exception handler
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from django.db import DatabaseError

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    自定义异常处理器
    Custom exception handler for REST framework

    Args:
        exc: 异常对象
        context: 上下文信息

    Returns:
        Response: 标准格式的错误响应
    """
    # 先调用DRF默认的异常处理
    response = exception_handler(exc, context)

    # 如果响应已存在，说明DRF已经处理了该异常
    if response is not None:
        # 记录错误日志
        logger.error(f"API Error: {exc} - {context['request'].path}")

        # 自定义响应格式
        custom_response_data = {
            'code': getattr(exc, 'code', response.status_code),
            'message': str(exc.detail) if hasattr(exc, 'detail') else str(exc),
            'data': None
        }

        # 处理验证错误
        if isinstance(exc.detail, dict):
            errors = {}
            for field, error_list in exc.detail.items():
                if isinstance(error_list, list):
                    errors[field] = error_list[0] if error_list else 'Validation error'
                else:
                    errors[field] = str(error_list)
            custom_response_data['message'] = 'Validation error'
            custom_response_data['data'] = errors
        elif isinstance(exc.detail, list):
            custom_response_data['message'] = exc.detail[0] if exc.detail else 'Validation error'

        response.data = custom_response_data
        return response

    # 处理Django内置异常
    if isinstance(exc, ValidationError):
        logger.error(f"Validation Error: {exc}")
        return Response({
            'code': status.HTTP_400_BAD_REQUEST,
            'message': 'Validation error',
            'data': {'detail': str(exc)}
        }, status=status.HTTP_400_BAD_REQUEST)

    # 处理数据库错误
    if isinstance(exc, DatabaseError):
        logger.error(f"Database Error: {exc}")
        return Response({
            'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            'message': 'Database error',
            'data': {'detail': 'An error occurred while processing your request'}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # 处理未知异常
    logger.exception(f"Unhandled Exception: {exc}")
    return Response({
        'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
        'message': 'Internal server error',
        'data': {'detail': str(exc) if settings.DEBUG else 'An unexpected error occurred'}
    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class APIException(Exception):
    """
    自定义API异常基类
    Custom API exception base class
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A server error occurred.'

    def __init__(self, detail=None, code=None):
        self.detail = detail or self.default_detail
        self.code = code or self.status_code
        super().__init__(self.detail)


class BusinessException(APIException):
    """
    业务异常
    Business logic exception
    """
    def __init__(self, detail, code=None, status_code=None):
        self.detail = detail
        self.code = code or status_code or status.HTTP_400_BAD_REQUEST
        super().__init__(detail, self.code)


class DeviceOfflineException(BusinessException):
    """设备离线异常"""
    pass


class AlarmThresholdExceededException(BusinessException):
    """告警阈值超出异常"""
    pass


class DataValidationException(BusinessException):
    """数据验证异常"""
    pass


# 导入settings
from django.conf import settings
