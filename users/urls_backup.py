from django.urls import path
from . import views
from . import admin_views
from django.contrib.auth import views as auth_views
from django.http import HttpResponse

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('logout-simple/', views.logout_view, name='logout_simple'),
    path('profile/', views.profile, name='profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('request-permission/', views.request_permission, name='request_permission'),
    path('permission-requests/', views.permission_requests, name='permission_requests'),
    path('permission-requests/<int:request_id>/approve/', views.approve_permission, name='approve_permission'),
    path('permission-requests/<int:request_id>/reject/', views.reject_permission, name='reject_permission'),
    
    # Admin URLs
    path('admin/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/test/', admin_views.admin_dashboard, name='test_admin'),
    path('admin/faculty-create/', admin_views.create_faculty, name='create_faculty'),
    path('admin/simple-test/', lambda request: HttpResponse("Simple test works!"), name='simple_test'),
    path('admin/create-faculty-test/', admin_views.create_faculty, name='create_faculty_test'),
    path('admin/users/', admin_views.user_management, name='user_management'),
    path('admin/users/<int:user_id>/', admin_views.user_detail, name='user_detail'),
    path('admin/users/<int:user_id>/promote/', admin_views.promote_to_admin, name='promote_to_admin'),
    path('admin/users/<int:user_id>/demote/', admin_views.demote_from_admin, name='demote_from_admin'),
    path('admin/users/<int:user_id>/change-role/', admin_views.change_user_role, name='change_user_role'),
    path('admin/users/<int:user_id>/delete/', admin_views.delete_user, name='delete_user'),
    path('admin/users/<int:user_id>/toggle-status/', admin_views.toggle_user_status, name='toggle_user_status'),
    path('admin/stats/', admin_views.system_stats, name='system_stats'),
]