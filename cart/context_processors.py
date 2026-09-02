from .views import get_or_create_cart

def cart(request):
    """Procesador de contexto para el carrito"""
    cart = get_or_create_cart(request)
    return {
        'cart': cart,
        'cart_total': cart.get_total(),
        'cart_items_count': cart.get_items_count(),
        'cart_items': cart.items.all()[:5],
    }