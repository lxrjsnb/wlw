"""
用户模块URL配置
User app URL configuration
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # 认证相关
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 用户信息
    path('user/', views.UserInfoView.as_view(), name='user_info'),
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),

    # 密码管理
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),

    # 登录日志
    path('login-logs/', views.UserLoginLogListView.as_view(), name='login_logs'),
    path('users/<int:user_id>/login-logs/', views.UserLoginLogListView.as_view(), name='user_login_logs'),
]
