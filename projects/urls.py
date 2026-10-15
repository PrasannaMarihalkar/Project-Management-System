from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list_view, name='project_list'),
    path('<int:project_id>/', views.project_detail_view, name='project_detail'),
    path('<int:project_id>/archive/', views.project_archive_view, name='project_archive'),
    path('<int:project_id>/members/', views.project_members_view, name='project_members'),
    path('<int:project_id>/members/<int:member_user_id>/role/', views.project_member_role_update_view, name='project_member_role_update'),
]
