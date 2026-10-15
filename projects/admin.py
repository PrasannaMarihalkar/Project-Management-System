from django.contrib import admin
from .models import Project, Membership

class MembershipInline(admin.TabularInline):
    model = Membership
    extra = 1

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'start_date', 'target_date', 'is_archived', 'created_at')
    list_filter = ('archived_at', 'created_at')
    search_fields = ('name', 'description', 'owner__email')
    inlines = [MembershipInline]

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('project', 'user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('project__name', 'user__email')
