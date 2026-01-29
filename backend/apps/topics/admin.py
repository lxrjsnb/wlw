from django.contrib import admin
from .models import Platform, Topic


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'color', 'is_active', 'sort_order', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active', 'sort_order', 'color']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'priority', 'owner', 'platform_count', 'post_count', 'created_at']
    list_filter = ['status', 'priority', 'platforms']
    search_fields = ['name', 'description']
    filter_horizontal = ['platforms']
    readonly_fields = ['created_at', 'updated_at']
