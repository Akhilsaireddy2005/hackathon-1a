from django.urls import path
from . import views

app_name = 'clubs'

urlpatterns = [
    path('', views.club_list, name='list'),
    path('create/', views.create_club, name='create'),
    path('<int:club_id>/', views.club_detail, name='detail'),
    path('<int:club_id>/join/', views.join_club, name='join'),
]