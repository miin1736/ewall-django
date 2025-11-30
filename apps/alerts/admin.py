"""
Alert admin
"""
from django.contrib import admin
from apps.alerts.models import Alert, EmailQueue


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['email', 'brand', 'category', 'active', 'created_at']
    list_filter = ['active', 'brand', 'category']
    search_fields = ['email']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'email', 'brand', 'category', 'active')
        }),
        ('조건', {
            'fields': ('conditions',),
            'description': 'JSON 형식으로 알림 조건 설정'
        }),
        ('메타', {
            'fields': ('created_at',)
        }),
    )


@admin.register(EmailQueue)
class EmailQueueAdmin(admin.ModelAdmin):
    list_display = ['to_email', 'subject', 'reason', 'sent', 'created_at']
    list_filter = ['sent', 'reason']
    search_fields = ['to_email', 'subject']
    readonly_fields = ['id', 'created_at', 'sent_at']
    
    fieldsets = (
        ('수신자 정보', {
            'fields': ('to_email', 'subject', 'reason')
        }),
        ('상품 정보', {
            'fields': ('product_id', 'product_data')
        }),
        ('발송 상태', {
            'fields': ('sent', 'sent_at', 'error')
        }),
        ('메타', {
            'fields': ('id', 'created_at')
        }),
    )
    
    def has_add_permission(self, request):
        # 이메일 큐는 시스템에서만 생성
        return False
