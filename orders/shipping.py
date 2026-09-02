from decimal import Decimal
from .interfaces import ShippingStrategy


class FreeShippingCalculator(ShippingStrategy):
    """Estrategia de envío gratis (estrategia por defecto actual)."""

    def calculate(self, subtotal: Decimal, items_count: int, **kwargs) -> Decimal:
        return Decimal('0.00')

    def get_description(self) -> str:
        return "Envío Estándar Gratuito"


class FlatRateShippingCalculator(ShippingStrategy):
    """Estrategia de tarifa plana fija (OCP)."""

    def __init__(self, flat_rate: Decimal = Decimal('99.00'), name: str = "Envío Exprés"):
        self.flat_rate = Decimal(str(flat_rate))
        self.name = name

    def calculate(self, subtotal: Decimal, items_count: int, **kwargs) -> Decimal:
        if items_count == 0:
            return Decimal('0.00')
        return self.flat_rate

    def get_description(self) -> str:
        return f"{self.name} (${self.flat_rate})"


class ThresholdFreeShippingCalculator(ShippingStrategy):
    """
    Estrategia de envío gratis condicional:
    Si el subtotal supera el umbral, envío gratis; si no, aplica tarifa base.
    """

    def __init__(
        self,
        threshold: Decimal = Decimal('999.00'),
        base_rate: Decimal = Decimal('120.00'),
        name: str = "Envío Nacional"
    ):
        self.threshold = Decimal(str(threshold))
        self.base_rate = Decimal(str(base_rate))
        self.name = name

    def calculate(self, subtotal: Decimal, items_count: int, **kwargs) -> Decimal:
        if items_count == 0:
            return Decimal('0.00')
        if subtotal >= self.threshold:
            return Decimal('0.00')
        return self.base_rate

    def get_description(self) -> str:
        return f"{self.name} (Gratis a partir de ${self.threshold})"
