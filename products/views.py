from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db import models
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from .models import Product, Category, Brand
from .forms import ProductForm, CategoryForm, BrandForm

class ProductListView(ListView):
    """Lista de productos con filtros"""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        # Búsqueda
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__icontains=search)
            )
        
        # Filtro por categoría
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            queryset = queryset.filter(category=category)
        
        # Filtro por marca
        brand_slug = self.request.GET.get('brand')
        if brand_slug:
            brand = get_object_or_404(Brand, slug=brand_slug)
            queryset = queryset.filter(brand=brand)
        
        # Filtro por precio
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Ordenamiento
        sort = self.request.GET.get('sort')
        if sort == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'popular':
            queryset = queryset.order_by('-sales', '-views')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['brands'] = Brand.objects.filter(is_active=True)
        
        # Filtros actuales para mostrarlos en la vista
        context['current_search'] = self.request.GET.get('search', '')
        context['current_sort'] = self.request.GET.get('sort', '')
        context['current_brand'] = self.request.GET.get('brand', '')
        context['current_min_price'] = self.request.GET.get('min_price', '')
        context['current_max_price'] = self.request.GET.get('max_price', '')
        
        # Título de la página
        if self.kwargs.get('category_slug'):
            category = get_object_or_404(Category, slug=self.kwargs['category_slug'])
            context['page_title'] = category.name
            context['category'] = category
        else:
            context['page_title'] = 'Todos los Productos'
        
        return context

class ProductDetailView(DetailView):
    """Detalle del producto"""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Incrementar vistas (usando F() para evitar race conditions y no guardar el objeto completo)
        Product.objects.filter(pk=product.pk).update(views=F('views') + 1)
        
        # Productos relacionados
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Variantes del producto
        context['variants'] = product.variants.filter(is_active=True)
        
        # Reseñas del producto
        context['reviews'] = product.reviews.filter(is_approved=True)
        
        # Calificación promedio
        context['average_rating'] = product.average_rating
        
        return context


@staff_member_required
def product_create(request):
    """Vista para crear un producto desde el frontend (solo staff)."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # Garantizar que el producto quede activo si el checkbox no se envió
            if 'is_active' not in request.POST:
                product.is_active = True
            product.save()
            form.save_m2m()
            messages.success(request, f'Producto "{product.name}" creado exitosamente.')
            return redirect('products:product_list')
        else:
            # Mostrar todos los errores de validación en los mensajes
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm()

    context = {
        'form': form,
        'page_title': 'Nuevo Producto',
        'action': 'create',
    }
    return render(request, 'products/product_form.html', context)


@staff_member_required
def product_edit(request, slug):
    """Vista para editar un producto existente desde el frontend (solo staff)."""
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Producto "{product.name}" actualizado exitosamente.')
            return redirect('products:product_detail', slug=product.slug)
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = ProductForm(instance=product)

    context = {
        'form': form,
        'product': product,
        'page_title': f'Editar: {product.name}',
        'action': 'edit',
    }
    return render(request, 'products/product_form.html', context)


@staff_member_required
def product_delete(request, slug):
    """Vista para eliminar un producto existente desde el frontend (solo staff)."""
    product = get_object_or_404(Product, slug=slug)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'El producto "{product_name}" fue eliminado exitosamente.')
        return redirect('products:product_list')

    return render(request, 'products/product_confirm_delete.html', {
        'product': product,
        'page_title': f'Eliminar: {product.name}',
    })


# ── Category views ────────────────────────────────────────────

@staff_member_required
def category_create(request):
    """Crear categoría desde el frontend (solo staff)."""
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" creada exitosamente.')
            return redirect('products:category_list')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CategoryForm()
    return render(request, 'products/category_form.html', {
        'form': form, 'page_title': 'Nueva Categoría', 'action': 'create'
    })


@staff_member_required
def category_edit(request, pk):
    """Editar categoría existente desde el frontend (solo staff)."""
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Categoría "{category.name}" actualizada.')
            return redirect('products:category_list')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'products/category_form.html', {
        'form': form, 'category': category,
        'page_title': f'Editar: {category.name}', 'action': 'edit'
    })


@staff_member_required
def category_list_manage(request):
    """Lista de categorías para gestión (solo staff)."""
    categories = Category.objects.all().order_by('order', 'name')
    return render(request, 'products/category_list_manage.html', {
        'categories': categories, 'page_title': 'Gestionar Categorías'
    })


# ── Brand views ───────────────────────────────────────────────

@staff_member_required
def brand_create(request):
    """Crear marca desde el frontend (solo staff)."""
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Marca "{brand.name}" creada exitosamente.')
            return redirect('products:brand_list')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = BrandForm()
    return render(request, 'products/brand_form.html', {
        'form': form, 'page_title': 'Nueva Marca', 'action': 'create'
    })


@staff_member_required
def brand_edit(request, pk):
    """Editar marca existente desde el frontend (solo staff)."""
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        form = BrandForm(request.POST, request.FILES, instance=brand)
        if form.is_valid():
            brand = form.save()
            messages.success(request, f'Marca "{brand.name}" actualizada.')
            return redirect('products:brand_list')
        else:
            messages.error(request, 'Por favor corrige los errores del formulario.')
    else:
        form = BrandForm(instance=brand)
    return render(request, 'products/brand_form.html', {
        'form': form, 'brand': brand,
        'page_title': f'Editar: {brand.name}', 'action': 'edit'
    })


@staff_member_required
def brand_list_manage(request):
    """Lista de marcas para gestión (solo staff)."""
    brands = Brand.objects.all().order_by('name')
    return render(request, 'products/brand_list_manage.html', {
        'brands': brands, 'page_title': 'Gestionar Marcas'
    })


# ── Stock / Inventario ────────────────────────────────────────

@staff_member_required
def stock_update(request, slug):
    """Actualización rápida de existencias de un producto (solo staff)."""
    product = get_object_or_404(Product, slug=slug)

    if request.method == 'POST':
        action = request.POST.get('action')
        quantity = request.POST.get('quantity', '0').strip()

        try:
            quantity = int(quantity)
        except ValueError:
            messages.error(request, 'La cantidad debe ser un número entero.')
            return redirect('products:stock_update', slug=slug)

        if quantity < 0:
            messages.error(request, 'La cantidad no puede ser negativa.')
            return redirect('products:stock_update', slug=slug)

        if action == 'set':
            # Establecer stock absoluto
            Product.objects.filter(pk=product.pk).update(stock=quantity)
            messages.success(request, f'Stock de "{product.name}" establecido a {quantity} unidades.')

        elif action == 'add':
            # Sumar al stock actual
            Product.objects.filter(pk=product.pk).update(stock=F('stock') + quantity)
            messages.success(request, f'Se agregaron {quantity} unidades a "{product.name}".')

        elif action == 'subtract':
            # Restar al stock actual (sin bajar de 0)
            new_stock = max(0, product.stock - quantity)
            Product.objects.filter(pk=product.pk).update(stock=new_stock)
            messages.success(request, f'Se descontaron {quantity} unidades de "{product.name}".')

        else:
            messages.error(request, 'Acción no reconocida.')

        return redirect('products:stock_update', slug=slug)

    # Recargar producto para obtener stock actualizado
    product.refresh_from_db()
    return render(request, 'products/stock_update.html', {
        'product': product,
        'page_title': f'Existencias: {product.name}',
    })


@staff_member_required
def stock_manage(request):
    """Panel de inventario completo — todos los productos (solo staff)."""
    products = Product.objects.all().order_by('name').select_related('category', 'brand')

    # Filtro rápido por estado de stock
    stock_filter = request.GET.get('stock', 'all')
    if stock_filter == 'out':
        products = products.filter(stock=0)
    elif stock_filter == 'low':
        products = products.filter(stock__gt=0, stock__lte=models.F('min_stock'))
    elif stock_filter == 'ok':
        products = products.filter(stock__gt=models.F('min_stock'))

    # Búsqueda
    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    return render(request, 'products/stock_manage.html', {
        'products': products,
        'stock_filter': stock_filter,
        'q': q,
        'page_title': 'Gestión de Inventario',
    })