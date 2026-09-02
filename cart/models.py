from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

class Cart(models.Model):
    """Modelo del carrito de compras"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField('Clave de sesión', max_length=40, blank=True, null=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Carrito'
        verbose_name_plural = 'Carritos'
    
    def __str__(self):
        return f"Carrito {self.id} - {self.user or 'Anónimo'}"
    
    def get_total(self):
        """Calcula el total del carrito"""
        return sum(item.get_total() for item in self.items.all())
    
    def get_total_without_discount(self):
        """Total sin descuentos"""
        return sum(item.get_subtotal() for item in self.items.all())
    
    def get_items_count(self):
        """Cantidad total de items"""
        return sum(item.quantity for item in self.items.all())
    
    def get_discount(self):
        """Total de descuentos"""
        return self.get_total_without_discount() - self.get_total()
    
    def clear(self):
        """Vacía el carrito"""
        self.items.all().delete()

class CartItem(models.Model):
    """Item del carrito"""
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    quantity = models.PositiveIntegerField('Cantidad', default=1)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Item del carrito'
        verbose_name_plural = 'Items del carrito'
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity}"
    
    def get_total(self):
        """Total del item con descuento"""
        return self.quantity * self.price
    
    def get_subtotal(self):
        """Subtotal sin descuento"""
        return self.quantity * self.product.price
    
    def get_discount(self):
        """Descuento aplicado al item"""
        return self.get_subtotal() - self.get_total()