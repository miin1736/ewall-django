"""
Analytics admin
"""
from django.contrib import admin
from apps.analytics.models import Click, DailyClickAggregate


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'brand', 'category', 'timestamp']
    list_filter = ['brand', 'category', 'timestamp']
    search_fields = ['product_id']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyClickAggregate)
class DailyClickAggregateAdmin(admin.ModelAdmin):
    list_display = ['date', 'brand', 'category', 'click_count', 'unique_products']
    list_filter = ['brand', 'category', 'date']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False
