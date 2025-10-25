from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('', views.event_list, name='list'),
    path('create/', views.create_event, name='create'),
    path('<int:event_id>/', views.event_detail, name='detail'),
    path('<int:event_id>/attend/', views.attend_event, name='attend'),
]