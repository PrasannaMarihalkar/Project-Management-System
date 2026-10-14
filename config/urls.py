"""
Project Management System URL Configuration
Maps both browser routes and REST API endpoints per SAD Section 4.3.
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='projects:project_list', permanent=False), name='index'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('projects/', include('projects.urls', namespace='projects')),
    path('tasks/', include('tasks.urls', namespace='tasks')),
    path('audit/', include('audit.urls', namespace='audit')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
]
