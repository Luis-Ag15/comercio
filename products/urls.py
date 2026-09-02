from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),

    # Rutas fijas — deben ir ANTES de los patrones <slug:slug>
    path('nuevo/', views.product_create, name='product_create'),
    path('inventario/', views.stock_manage, name='stock_manage'),

    # Category management
    path('categorias/', views.category_list_manage, name='category_list'),
    path('categorias/nueva/', views.category_create, name='category_create'),
    path('categorias/<int:pk>/editar/', views.category_edit, name='category_edit'),

    # Brand management
    path('marcas/', views.brand_list_manage, name='brand_list'),
    path('marcas/nueva/', views.brand_create, name='brand_create'),
    path('marcas/<int:pk>/editar/', views.brand_edit, name='brand_edit'),

    # Category filter (also fixed prefix, safe)
    path('category/<slug:category_slug>/', views.ProductListView.as_view(), name='category_detail'),

    # Rutas con slug de producto — al final
    path('<slug:slug>/editar/', views.product_edit, name='product_edit'),
    path('<slug:slug>/existencias/', views.stock_update, name='stock_update'),
    path('<slug:slug>/eliminar/', views.product_delete, name='product_delete'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
]