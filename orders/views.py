from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.db.models import Q, Sum, Count
from cart.views import get_or_create_cart
from core.models import AuditLog
from .models import Order, OrderItem
from .forms import OrderCreateForm
from .services import CheckoutService


def order_create(request, checkout_service=None):
    """Vista de Checkout delgada para crear y finalizar un pedido (SRP)."""
    checkout_service = checkout_service or CheckoutService()
    cart = get_or_create_cart(request)
    
    if cart.get_items_count() == 0:
        messages.warning(request, 'Tu carrito de compras está vacío. Agrega productos antes de realizar el pedido.')
        return redirect('cart:cart_detail')
    
    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            try:
                order = checkout_service.create_order(
                    cart=cart,
                    form=form,
                    user=request.user,
                    request=request
                )
                request.session['last_order_id'] = order.id
                messages.success(request, f'¡Pedido #{order.id} creado con éxito! Hemos enviado un correo de confirmación.')
                return redirect('orders:order_created', order_id=order.id)
            except Exception as e:
                messages.error(request, f'Ocurrió un error al procesar tu pedido: {str(e)}')
    else:
        # Prellenar datos si el usuario está autenticado
        initial_data = {}
        if request.user.is_authenticated:
            initial_data['first_name'] = request.user.first_name
            initial_data['last_name'] = request.user.last_name
            initial_data['email'] = request.user.email
            initial_data['phone'] = getattr(request.user, 'phone', '')
            
            # Datos desde el perfil si existe
            if hasattr(request.user, 'profile'):
                profile = request.user.profile
                initial_data['address'] = profile.street
                initial_data['city'] = profile.city
                initial_data['state'] = profile.state
                initial_data['country'] = profile.country or 'México'
                initial_data['postal_code'] = profile.postal_code
                
        form = OrderCreateForm(initial=initial_data)
    
    context = {
        'cart': cart,
        'form': form,
        'items': cart.items.all(),
        'total': cart.get_total(),
        'total_items': cart.get_items_count(),
    }
    return render(request, 'orders/order_create.html', context)

def order_created(request, order_id):
    """Página de éxito tras completar el pedido"""
    order = get_object_or_404(Order, id=order_id)
    
    # Comprobar permisos básicos (usuario dueño o pedido recién creado en la sesión actual)
    if request.user.is_authenticated and order.user and order.user != request.user:
        if request.session.get('last_order_id') != order.id:
            messages.error(request, 'No tienes permiso para ver este pedido.')
            return redirect('core:home')
    
    return render(request, 'orders/order_created.html', {'order': order})

@login_required
def order_list(request):
    """Historial de pedidos del usuario autenticado"""
    orders = Order.objects.filter(user=request.user)
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_detail(request, order_id):
    """Detalle de un pedido específico para el cliente"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


# ─── PANEL DE ADMINISTRACIÓN DE PEDIDOS ──────────────────────────────────────

def is_staff(user):
    return user.is_active and (user.is_staff or user.is_superuser)

@login_required
@user_passes_test(is_staff, login_url='/')
def panel_order_list(request):
    """Panel de gestión de pedidos — solo para staff/admin"""
    orders = Order.objects.all().select_related('user')

    # Filtros
    status_filter = request.GET.get('status', '')
    payment_filter = request.GET.get('payment_status', '')
    search = request.GET.get('q', '').strip()

    if status_filter:
        orders = orders.filter(status=status_filter)
    if payment_filter:
        orders = orders.filter(payment_status=payment_filter)
    if search:
        orders = orders.filter(
            Q(id__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(tracking_number__icontains=search)
        )

    # Estadísticas generales
    all_orders = Order.objects.all()
    stats = {
        'total':      all_orders.count(),
        'pending':    all_orders.filter(status='pending').count(),
        'processing': all_orders.filter(status='processing').count(),
        'shipped':    all_orders.filter(status='shipped').count(),
        'delivered':  all_orders.filter(status='delivered').count(),
        'cancelled':  all_orders.filter(status='cancelled').count(),
        'revenue':    all_orders.filter(payment_status='paid').aggregate(t=Sum('total'))['t'] or 0,
    }

    context = {
        'orders': orders,
        'stats': stats,
        'status_filter': status_filter,
        'payment_filter': payment_filter,
        'search': search,
        'status_choices': Order.STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'orders/panel/order_list.html', context)


@login_required
@user_passes_test(is_staff, login_url='/')
def panel_order_detail(request, order_id):
    """Detalle de pedido para el panel staff — permite actualizar estado y guía"""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        new_payment_status = request.POST.get('payment_status')
        tracking_number = request.POST.get('tracking_number', '').strip()

        # Capturar valores anteriores para la bitácora
        changes = {}
        if new_status in dict(Order.STATUS_CHOICES) and new_status != order.status:
            changes['status'] = {'before': order.status, 'after': new_status}
            order.status = new_status
        if new_payment_status in dict(Order.PAYMENT_STATUS_CHOICES) and new_payment_status != order.payment_status:
            changes['payment_status'] = {'before': order.payment_status, 'after': new_payment_status}
            order.payment_status = new_payment_status
        if tracking_number != order.tracking_number:
            changes['tracking_number'] = {'before': order.tracking_number, 'after': tracking_number}
        order.tracking_number = tracking_number
        order.save()

        # Registrar en bitácora solo si hubo cambios reales
        if changes:
            try:
                AuditLog.log(
                    AuditLog.EVENT_ORDER_UPDATED,
                    user=request.user,
                    request=request,
                    obj=order,
                    object_repr=str(order),
                    changes=changes,
                )
            except Exception:
                pass

        messages.success(request, f'Pedido #{order.id} actualizado correctamente.')
        return redirect('orders:panel_order_detail', order_id=order.id)

    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        'payment_choices': Order.PAYMENT_STATUS_CHOICES,
    }
    return render(request, 'orders/panel/order_detail.html', context)

