"""
帖子模块URL配置
Post app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'posts'

router = DefaultRouter()
router.register(r'summaries', views.PostSummaryViewSet, basename='post_summary')
router.register(r'', views.SocialPostViewSet, basename='social_post')

urlpatterns = [
    path('', include(router.urls)),
]
