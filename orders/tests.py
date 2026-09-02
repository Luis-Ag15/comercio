from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from products.models import Product, Category
from products.services import InventoryService
from cart.models import Cart, CartItem
from cart.services import CartService
from orders.models import Order
from orders.forms import OrderCreateForm
from orders.interfaces import OrderNotifier
from orders.shipping import (
    FreeShippingCalculator,
    FlatRateShippingCalculator,
    ThresholdFreeShippingCalculator,
)
from orders.services import CheckoutService

User = get_user_model()


class MockOrderNotifier(OrderNotifier):
    """Notificador simulado para pruebas unitarias sin dependencias externas (DIP)."""
    def __init__(self):
        self.notified_orders = []

    def notify_order_placed(self, order, request=None) -> bool:
        self.notified_orders.append(order)
        return True


class SolidArchitectureTests(TestCase):
    """
    Suite de pruebas que valida el cumplimiento de los principios SOLID:
    - SRP: InventoryService, CartService y CheckoutService con responsabilidades únicas.
    - OCP/LSP: Estrategias de envío polimórficas e intercambiables.
    - DIP: Inyección de MockOrderNotifier y estrategias de envío sin dependencias duras.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username='soliduser',
            email='solid@example.com',
            password='testpassword123'
        )
        self.category = Category.objects.create(name='Vasos', slug='vasos')
        self.product = Product.objects.create(
            name='Vaso Térmico 500ml',
            slug='vaso-termico-500ml',
            sku='VASO-001',
            category=self.category,
            price=Decimal('200.00'),
            stock=10,
            sales=0
        )

    # ── 1. Single Responsibility Principle (SRP) en InventoryService ──
    def test_inventory_service_deducts_stock_and_accumulates_sales(self):
        new_stock = InventoryService.deduct_stock(self.product, 3)
        self.assertEqual(new_stock, 7)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 7)
        self.assertEqual(self.product.sales, 3)

    def test_inventory_service_raises_validation_error_when_exceeding_stock(self):
        with self.assertRaises(ValidationError):
            InventoryService.deduct_stock(self.product, 15)

    # ── 2. Open/Closed Principle (OCP) y Liskov (LSP) en Envíos ───────
    def test_shipping_strategies_polymorphism(self):
        subtotal = Decimal('500.00')
        items_count = 2

        free = FreeShippingCalculator()
        flat = FlatRateShippingCalculator(flat_rate=Decimal('80.00'))
        threshold = ThresholdFreeShippingCalculator(threshold=Decimal('600.00'), base_rate=Decimal('100.00'))

        # Verificamos que todas responden al mismo contrato (LSP)
        self.assertEqual(free.calculate(subtotal, items_count), Decimal('0.00'))
        self.assertEqual(flat.calculate(subtotal, items_count), Decimal('80.00'))
        self.assertEqual(threshold.calculate(subtotal, items_count), Decimal('100.00'))

        # Superando el umbral
        self.assertEqual(threshold.calculate(Decimal('700.00'), items_count), Decimal('0.00'))

    # ── 3. CartService (SRP) ──────────────────────────────────────────
    def test_cart_service_add_and_clear(self):
        cart = CartService.get_or_create_cart(user=self.user)
        item, created = CartService.add_item(cart, self.product, quantity=2)
        self.assertTrue(created)
        self.assertEqual(cart.get_items_count(), 2)
        self.assertEqual(cart.get_total(), Decimal('400.00'))

        CartService.clear_cart(cart)
        self.assertEqual(cart.get_items_count(), 0)

    # ── 4. Dependency Inversion (DIP) en CheckoutService ───────────────
    def test_checkout_service_with_injected_dependencies(self):
        cart = CartService.get_or_create_cart(user=self.user)
        CartService.add_item(cart, self.product, quantity=2)

        mock_notifier = MockOrderNotifier()
        custom_shipping = FlatRateShippingCalculator(flat_rate=Decimal('50.00'))

        checkout_service = CheckoutService(
            shipping_calculator=custom_shipping,
            notifier=mock_notifier
        )

        form_data = {
            'first_name': 'Juan',
            'last_name': 'Pérez',
            'email': 'juan@example.com',
            'phone': '5512345678',
            'address': 'Av. Principal 123',
            'city': 'Guadalajara',
            'state': 'Jalisco',
            'country': 'México',
            'postal_code': '44100',
            'payment_method': 'cod'
        }
        form = OrderCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

        order = checkout_service.create_order(
            cart=cart,
            form=form,
            user=self.user
        )

        # Verificaciones:
        # 1. Total con tarifa de envío personalizada (OCP)
        # Subtotal: 400.00 + Envío: 50.00 = 450.00
        self.assertEqual(order.subtotal, Decimal('400.00'))
        self.assertEqual(order.shipping_cost, Decimal('50.00'))
        self.assertEqual(order.total, Decimal('450.00'))

        # 2. Stock descontado mediante InventoryService (SRP)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 8)
        self.assertEqual(self.product.sales, 2)

        # 3. Carrito vaciado (SRP)
        self.assertEqual(cart.get_items_count(), 0)

        # 4. Notificador desacoplado notificado (DIP)
        self.assertEqual(len(mock_notifier.notified_orders), 1)
        self.assertEqual(mock_notifier.notified_orders[0].id, order.id)
