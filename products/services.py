from typing import Protocol, runtime_checkable
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import transaction


@runtime_checkable
class Stockable(Protocol):
    """Protocolo que define los requerimientos mínimos para un artículo con inventario (ISP)."""
    id: int
    name: str
    stock: int
    sales: int


class InventoryService:
    """
    Servicio responsable exclusivamente del control y mutación de existencias (SRP).
    """

    @staticmethod
    def check_availability(item: Stockable, quantity: int) -> bool:
        """Verifica si hay suficiente inventario disponible sin alterar estado."""
        if quantity <= 0:
            return False
        return item.stock >= quantity

    @staticmethod
    def validate_or_raise(item: Stockable, quantity: int) -> None:
        """Lanza ValidationError si no hay inventario suficiente."""
        if quantity <= 0:
            raise ValidationError("La cantidad solicitada debe ser mayor a 0.")
        if item.stock < quantity:
            raise ValidationError(
                f"Inventario insuficiente para '{item.name}'. "
                f"Disponibles: {item.stock}, solicitadas: {quantity}."
            )

    @classmethod
    @transaction.atomic
    def deduct_stock(cls, product, quantity: int) -> int:
        """
        Descuenta inventario y acumula ventas de manera atómica.
        Retorna el nuevo stock restante.
        """
        cls.validate_or_raise(product, quantity)
        product.stock -= quantity
        if hasattr(product, 'sales'):
            product.sales += quantity
            product.save(update_fields=['stock', 'sales'])
        else:
            product.save(update_fields=['stock'])
        return product.stock

    @classmethod
    @transaction.atomic
    def restore_stock(cls, product, quantity: int) -> int:
        """
        Restaura existencias (ej. ante cancelaciones de orden).
        """
        if quantity <= 0:
            return product.stock
        product.stock += quantity
        if hasattr(product, 'sales') and product.sales >= quantity:
            product.sales -= quantity
            product.save(update_fields=['stock', 'sales'])
        else:
            product.save(update_fields=['stock'])
        return product.stock
