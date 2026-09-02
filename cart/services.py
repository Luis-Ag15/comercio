from decimal import Decimal
from typing import Tuple, Optional
from django.core.exceptions import ValidationError
from django.db import transaction

from products.models import Product
from products.services import InventoryService
from .models import Cart, CartItem


class CartService:
    """
    Servicio de dominio para todas las operaciones relacionadas con el carrito (SRP).
    Aisla la lógica de negocio de las vistas controladoras.
    """

    @classmethod
    def get_or_create_cart(cls, user=None, session=None) -> Cart:
        """Obtiene o crea un carrito según el estado de autenticación o sesión."""
        if user and user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
            if session and session.session_key:
                session_cart = Cart.objects.filter(session_key=session.session_key).first()
                if session_cart and session_cart != cart:
                    cls.merge_carts(session_cart, cart)
            return cart

        if session:
            if not session.session_key:
                session.create()
            cart, _ = Cart.objects.get_or_create(session_key=session.session_key)
            return cart

        raise ValueError("Se requiere un usuario o una sesión válida para obtener el carrito.")

    @classmethod
    @transaction.atomic
    def merge_carts(cls, source_cart: Cart, target_cart: Cart) -> None:
        """Fusiona los elementos del carrito de sesión al carrito del usuario."""
        if not source_cart or not target_cart or source_cart.id == target_cart.id:
            return

        for source_item in source_cart.items.select_related('product'):
            target_item, created = CartItem.objects.get_or_create(
                cart=target_cart,
                product=source_item.product,
                defaults={
                    'quantity': source_item.quantity,
                    'price': source_item.price
                }
            )
            if not created:
                target_item.quantity += source_item.quantity
                target_item.save()

        source_cart.delete()

    @classmethod
    def add_item(cls, cart: Cart, product: Product, quantity: int = 1) -> Tuple[CartItem, bool]:
        """
        Añade un producto al carrito validando stock con InventoryService.
        Retorna (cart_item, created).
        """
        if not product.is_active:
            raise ValidationError("El producto no está disponible para compra.")

        if quantity <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0.")

        price = product.discount_price if product.discount_price else product.price

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity, 'price': price}
        )

        if not created:
            total_quantity = cart_item.quantity + quantity
            InventoryService.validate_or_raise(product, total_quantity)
            cart_item.quantity = total_quantity
            cart_item.price = price
            cart_item.save()
        else:
            InventoryService.validate_or_raise(product, quantity)
            cart_item.price = price
            cart_item.save()

        return cart_item, created

    @classmethod
    def update_item_quantity(cls, cart: Cart, item_id: int, quantity: int) -> Optional[CartItem]:
        """Actualiza la cantidad de un ítem existente o lo elimina si quantity <= 0."""
        try:
            item = cart.items.select_related('product').get(id=item_id)
        except CartItem.DoesNotExist:
            return None

        if quantity <= 0:
            item.delete()
            return None

        InventoryService.validate_or_raise(item.product, quantity)
        item.quantity = quantity
        item.save(update_fields=['quantity'])
        return item

    @classmethod
    def remove_item(cls, cart: Cart, item_id: int) -> bool:
        """Elimina un ítem específico del carrito."""
        deleted_count, _ = cart.items.filter(id=item_id).delete()
        return deleted_count > 0

    @classmethod
    def clear_cart(cls, cart: Cart) -> None:
        """Vacía el contenido del carrito."""
        cart.clear()
