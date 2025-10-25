from django.urls import path
from . import views

app_name = 'feedback'

urlpatterns = [
    path('', views.feedback_list, name='list'),
    path('create/', views.create_feedback, name='create'),
    path('<int:feedback_id>/', views.feedback_detail, name='detail'),
]