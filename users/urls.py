from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

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
    path('permission-requests/<int:request_id>/', views.permission_request_detail, name='permission_request_detail'),
    path('permission-requests/<int:request_id>/approve/', views.approve_permission, name='approve_permission'),
    path('permission-requests/<int:request_id>/reject/', views.reject_permission, name='reject_permission'),
    path('create-user/', views.create_user, name='create_user'),
]