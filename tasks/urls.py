from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Project-scoped Task routes
    path('projects/<int:project_id>/tasks/', views.task_list_create_view, name='task_list_create'),
    path('projects/<int:project_id>/tasks/<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('projects/<int:project_id>/tasks/<int:task_id>/status/', views.task_status_transition_view, name='task_status_transition'),
    path('projects/<int:project_id>/tasks/<int:task_id>/time/', views.task_time_log_view, name='task_time_log'),
    path('projects/<int:project_id>/tasks/<int:task_id>/time/<int:entry_id>/', views.time_entry_detail_view, name='time_entry_detail'),
    path('projects/<int:project_id>/tasks/<int:task_id>/comments/', views.task_comment_create_view, name='task_comment_create'),
    path('projects/<int:project_id>/dashboard/', views.project_dashboard_api, name='project_dashboard'),
    path('projects/<int:project_id>/tasks.csv', views.project_tasks_csv_view, name='project_tasks_csv'),
]
