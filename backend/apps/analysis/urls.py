"""
分析模块URL配置
Analysis app URL configuration
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'analysis'

router = DefaultRouter()
router.register(r'logs', views.AnalysisLogViewSet, basename='analysis_log')
router.register(r'', views.AnalysisViewSet, basename='analysis')

# 新增深度分析ViewSet
router.register(r'hotness', views.HotnessViewSet, basename='hotness')
router.register(r'propagation', views.PropagationViewSet, basename='propagation')
router.register(r'emergency', views.EmergencyViewSet, basename='emergency')
router.register(r'kol', views.KOLViewSet, basename='kol')
router.register(r'evolution', views.EvolutionViewSet, basename='evolution')
router.register(r'sentiment', views.SentimentAnalysisViewSet, basename='sentiment')

urlpatterns = [
    path('', include(router.urls)),
]
