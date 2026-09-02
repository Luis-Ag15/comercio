from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from products.models import Product
from .models import Cart, CartItem
from .services import CartService


def get_or_create_cart(request):
    """
    Función de compatibilidad que delega a CartService (SRP/DIP).
    Permite a otras apps y vistas obtener el carrito sin acoplarse a la implementación de sesión/BD.
    """
    return CartService.get_or_create_cart(user=request.user, session=request.session)


def merge_carts(source_cart, target_cart):
    """Compatibilidad con código anterior que llamaba a merge_carts directamente."""
    CartService.merge_carts(source_cart, target_cart)


def cart_detail(request):
    """Vista controladora que presenta el carrito actual."""
    cart = get_or_create_cart(request)
    context = {
        'cart': cart,
        'items': cart.items.all(),
        'total': cart.get_total(),
        'total_items': cart.get_items_count(),
    }
    return render(request, 'cart/cart_detail.html', context)


@require_POST
def add_to_cart(request, product_id):
    """Controlador HTTP para añadir productos delegando en CartService."""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_or_create_cart(request)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    try:
        CartService.add_item(cart, product, quantity)
        messages.success(request, f'{product.name} añadido al carrito.')
    except ValidationError as e:
        messages.error(request, e.message if hasattr(e, 'message') else str(e))
        return redirect('products:product_detail', slug=product.slug)

    # Si es AJAX, devolver JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} añadido al carrito',
            'cart_total': cart.get_items_count(),
        })

    return redirect('cart:cart_detail')


@require_POST
def update_cart_item(request, item_id):
    """Controlador HTTP para actualizar cantidad de un ítem."""
    cart = get_or_create_cart(request)
    try:
        quantity = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1

    try:
        updated_item = CartService.update_item_quantity(cart, item_id, quantity)
        if updated_item is None:
            messages.info(request, 'Item removido del carrito.')
        else:
            messages.success(request, 'Carrito actualizado.')
    except ValidationError as e:
        messages.error(request, e.message if hasattr(e, 'message') else str(e))

    return redirect('cart:cart_detail')


@require_POST
def remove_from_cart(request, item_id):
    """Controlador HTTP para remover un ítem del carrito."""
    cart = get_or_create_cart(request)
    item = cart.items.filter(id=item_id).first()
    product_name = item.product.name if item else 'Producto'

    CartService.remove_item(cart, item_id)
    messages.success(request, f'{product_name} removido del carrito.')
    return redirect('cart:cart_detail')


def cart_widget(request):
    """Widget del carrito para el header."""
    cart = get_or_create_cart(request)
    return render(request, 'cart/cart_widget.html', {
        'cart_items': cart.items.all()[:5],
        'total_items': cart.get_items_count(),
        'total': cart.get_total()
    })