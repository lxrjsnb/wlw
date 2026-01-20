"""
自定义分页类
Custom pagination classes
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    标准分页类
    Standard pagination with custom response format
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        自定义分页响应格式
        Custom pagination response format
        """
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'items': data,
                'total': self.page.paginator.count,
                'page': self.page.number,
                'page_size': self.get_page_size(self.request),
                'total_pages': self.page.paginator.num_pages,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })


class LargeResultsSetPagination(PageNumberPagination):
    """
    大结果集分页 - 用于数据导出等场景
    Large result set pagination
    """
    page_size = 100
    page_size_query_param = 'page_size'
    max_page_size = 1000
