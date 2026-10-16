from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'recipient', 'title', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('recipient__email', 'title', 'message')
