from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.order_create, name='order_create'),
    path('created/<int:order_id>/', views.order_created, name='order_created'),
    path('history/', views.order_list, name='order_list'),
    path('<int:order_id>/', views.order_detail, name='order_detail'),

    # Panel de gestión (solo staff)
    path('panel/', views.panel_order_list, name='panel_order_list'),
    path('panel/<int:order_id>/', views.panel_order_detail, name='panel_order_detail'),
]
