import logging
from decimal import Decimal
from typing import Optional
from django.db import transaction
from django.core.exceptions import ValidationError

from core.models import AuditLog
from products.services import InventoryService
from cart.services import CartService
from .models import Order, OrderItem
from .interfaces import ShippingStrategy, OrderNotifier
from .shipping import FreeShippingCalculator
from .emails import send_order_admin_notification, send_order_customer_confirmation

logger = logging.getLogger(__name__)


class EmailOrderNotifier(OrderNotifier):
    """
    Implementación concreta de OrderNotifier para envío de correos (SRP / DIP).
    Aisla la lógica de entrega de correos del proceso de compra.
    """

    def notify_order_placed(self, order: Order, request=None) -> bool:
        admin_ok = False
        customer_ok = False
        try:
            admin_ok = send_order_admin_notification(order, request)
        except Exception as e:
            logger.error(f"Error enviando notificación al admin para orden #{order.id}: {e}")

        try:
            customer_ok = send_order_customer_confirmation(order)
        except Exception as e:
            logger.error(f"Error enviando confirmación al cliente para orden #{order.id}: {e}")

        return admin_ok or customer_ok


class CheckoutService:
    """
    Servicio de Dominio para el proceso de Checkout y creación de pedidos (SRP / DIP).
    Coordina la transacción atómica, inventario, costos de envío y notificaciones.
    """

    def __init__(
        self,
        shipping_calculator: Optional[ShippingStrategy] = None,
        inventory_service=InventoryService,
        cart_service=CartService,
        notifier: Optional[OrderNotifier] = None,
    ):
        # Inyección de Dependencias (DIP) con fallbacks razonables por defecto
        self.shipping_calculator = shipping_calculator or FreeShippingCalculator()
        self.inventory_service = inventory_service
        self.cart_service = cart_service
        self.notifier = notifier or EmailOrderNotifier()

    @transaction.atomic
    def create_order(self, cart, form, user=None, request=None) -> Order:
        """
        Ejecuta la orquestación completa de la orden:
        1. Validar carrito
        2. Validar existencias de todos los ítems antes de proceder
        3. Crear orden y asignar subtotales/envío calculado por la estrategia
        4. Crear OrderItems y descontar existencias
        5. Vaciar carrito
        6. Disparar notificaciones
        """
        cart_items = list(cart.items.select_related('product').all())
        if not cart_items:
            raise ValidationError("El carrito de compras está vacío.")

        # 1. Pre-validación de existencias completas
        for item in cart_items:
            if not item.product:
                raise ValidationError("Uno de los productos en el carrito ya no existe.")
            self.inventory_service.validate_or_raise(item.product, item.quantity)

        # 2. Instanciar la orden a partir del formulario
        order = form.save(commit=False)
        if user and user.is_authenticated:
            order.user = user

        subtotal = cart.get_total_without_discount()
        discount = cart.get_discount()
        items_count = cart.get_items_count()

        # Cálculo de envío abierto a extensión (OCP)
        shipping_cost = self.shipping_calculator.calculate(
            subtotal=subtotal,
            items_count=items_count
        )

        order.subtotal = subtotal
        order.discount = discount
        order.shipping_cost = shipping_cost
        order.total = (subtotal - discount) + shipping_cost
        order.save(force_insert=True)

        # 3. Creación de ítems y deducción de existencias
        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                product_sku=getattr(item.product, 'sku', '') or '',
                price=item.price,
                quantity=item.quantity
            )
            self.inventory_service.deduct_stock(item.product, item.quantity)

        # 4. Vaciar carrito
        self.cart_service.clear_cart(cart)

        # 5. Notificaciones (desacopladas)
        if self.notifier:
            self.notifier.notify_order_placed(order, request=request)

        # 6. Registro de auditoría
        try:
            AuditLog.log(
                AuditLog.EVENT_ORDER_CREATED,
                user=user if user and user.is_authenticated else None,
                request=request,
                obj=order,
                object_repr=str(order),
                extra={
                    'total': str(order.total),
                    'items': order.get_items_count(),
                    'payment_method': order.payment_method,
                },
            )
        except Exception as e:
            logger.error(f"Error registrando auditoría de creación de orden #{order.id}: {e}")

        return order
