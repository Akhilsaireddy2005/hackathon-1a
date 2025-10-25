from django.urls import path
from . import views

app_name = 'lost_found'

urlpatterns = [
    path('', views.item_list, name='list'),
    path('create/', views.create_item, name='create'),
    path('<int:item_id>/', views.item_detail, name='detail'),
    path('<int:item_id>/update/', views.update_item, name='update'),
    path('<int:item_id>/delete/', views.delete_item, name='delete'),
]