from django.urls import path
from . import views

app_name = 'audit'

urlpatterns = [
    path('projects/<int:project_id>/activity/', views.project_activity_api, name='project_activity_api'),
]
