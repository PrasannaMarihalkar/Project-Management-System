from django.contrib import admin
from .models import ActivityEvent

@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'project', 'actor', 'action', 'entity_type', 'entity_id')
    list_filter = ('action', 'entity_type', 'created_at', 'project')
    search_fields = ('details', 'actor__email', 'entity_id')
    readonly_fields = ('created_at',)
