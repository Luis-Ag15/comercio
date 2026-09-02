from abc import ABC, abstractmethod
from decimal import Decimal
from typing import NamedTuple, Optional, Any


class PaymentResult(NamedTuple):
    """Resultado estandarizado de una operación de pago (LSP/ISP)."""
    success: bool
    transaction_id: str = ""
    message: str = ""
    raw_response: Optional[Any] = None


class ShippingStrategy(ABC):
    """
    Abstracción base para el cálculo de costos de envío (OCP / LSP).
    Permite incorporar nuevas paqueterías o reglas de envío sin modificar las órdenes ni vistas.
    """

    @abstractmethod
    def calculate(self, subtotal: Decimal, items_count: int, **kwargs) -> Decimal:
        """Calcula el costo del envío."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Descripción legible del método de envío."""
        pass


class PaymentGateway(ABC):
    """
    Abstracción base para pasarelas de pago (OCP / DIP).
    """

    @abstractmethod
    def process_payment(self, order, payment_data: Optional[dict] = None) -> PaymentResult:
        """Procesa el pago de una orden."""
        pass


class OrderNotifier(ABC):
    """
    Abstracción para la notificación de eventos sobre pedidos (DIP).
    Permite desacoplar el envío de emails, SMS o Webhooks del flujo de creación del pedido.
    """

    @abstractmethod
    def notify_order_placed(self, order, request=None) -> bool:
        """Envía notificaciones cuando un pedido es creado."""
        pass
