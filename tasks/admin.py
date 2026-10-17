from django.contrib import admin
from .models import Task, TimeEntry, Comment

class TimeEntryInline(admin.TabularInline):
    model = TimeEntry
    extra = 0

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'project', 'status', 'priority', 'assignee', 'estimate_hours', 'due_date', 'version')
    list_filter = ('status', 'priority', 'project', 'created_at')
    search_fields = ('title', 'description', 'assignee__email')
    inlines = [TimeEntryInline, CommentInline]

@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ('task', 'user', 'hours', 'date', 'created_at')
    list_filter = ('date', 'created_at')
    search_fields = ('note', 'user__email', 'task__title')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    search_fields = ('text', 'author__email', 'task__title')
