from django.db import models
from django.conf import settings
from products.models import Product
from core.encryption import EncryptedCharField

class Order(models.Model):
    """Modelo de orden o pedido"""
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('processing', 'En proceso'),
        ('shipped', 'Enviado'),
        ('delivered', 'Entregado'),
        ('cancelled', 'Cancelado'),
    )
    
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('paid', 'Pagado'),
        ('failed', 'Fallido'),
        ('refunded', 'Reembolsado'),
    )
    
    PAYMENT_METHOD_CHOICES = (
        ('cod', 'Contra entrega / Efectivo'),
        ('transfer', 'Transferencia bancaria'),
        ('card', 'Tarjeta de crédito / débito'),
        ('paypal', 'PayPal'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Usuario'
    )
    
    # Datos del cliente / envío — cifrados en la BD
    first_name = EncryptedCharField('Nombre')
    last_name = EncryptedCharField('Apellido')
    email = models.EmailField('Correo electrónico')
    birth_date = models.DateField('Fecha de nacimiento', blank=True, null=True)
    phone = EncryptedCharField('Teléfono', blank=True, default='')
    address = EncryptedCharField('Dirección')
    city = EncryptedCharField('Ciudad')
    state = EncryptedCharField('Estado / Provincia')
    postal_code = EncryptedCharField('Código postal')
    country = EncryptedCharField('País', default='México')
    order_notes = models.TextField('Notas del pedido', blank=True)
    
    # Información de estado y pagos
    status = models.CharField('Estado', max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField('Estado del pago', max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    payment_method = models.CharField('Método de pago', max_length=20, choices=PAYMENT_METHOD_CHOICES, default='cod')
    
    # Importes financieros
    subtotal = models.DecimalField('Subtotal', max_digits=10, decimal_places=2, default=0.00)
    discount = models.DecimalField('Descuento', max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField('Costo de envío', max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField('Total', max_digits=10, decimal_places=2, default=0.00)
    
    tracking_number = models.CharField('Número de seguimiento', max_length=100, blank=True)
    
    created_at = models.DateTimeField('Fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('Última actualización', auto_now=True)
    
    class Meta:
        verbose_name = 'Pedido'
        verbose_name_plural = 'Pedidos'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pedido #{self.id} - {self.get_full_name()} (${self.total})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_items_count(self):
        return sum(item.quantity for item in self.items.all())
    
    def get_total_cost(self):
        return sum(item.get_cost() for item in self.items.all())

class OrderItem(models.Model):
    """Ítem o producto dentro de un pedido"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Pedido'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items',
        verbose_name='Producto'
    )
    product_name = models.CharField('Nombre del producto', max_length=255, blank=True)
    product_sku = models.CharField('SKU', max_length=50, blank=True)
    price = models.DecimalField('Precio unitario', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Cantidad', default=1)
    
    class Meta:
        verbose_name = 'Artículo del pedido'
        verbose_name_plural = 'Artículos del pedido'
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name or (self.product.name if self.product else 'Producto')}"
    
    def get_cost(self):
        return self.price * self.quantity
