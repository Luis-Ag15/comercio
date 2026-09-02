"""
Signals de auditoría para la app core.

Captura automáticamente:
  - Inicio de sesión exitoso
  - Cierre de sesión
  - Intento de login fallido
  - Creación y modificación de Productos
"""
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.db.models.signals import post_save
from django.dispatch import receiver


# ──────────────────────────────────────────────────────────────────────────────
# Signals de autenticación
# ──────────────────────────────────────────────────────────────────────────────

@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    from .models import AuditLog
    AuditLog.log(
        AuditLog.EVENT_LOGIN_SUCCESS,
        user=user,
        request=request,
        object_repr=f'Usuario: {user.email}',
        extra={'username': user.email},
    )


@receiver(user_logged_out)
def on_user_logged_out(sender, request, user, **kwargs):
    from .models import AuditLog
    AuditLog.log(
        AuditLog.EVENT_LOGOUT,
        user=user,
        request=request,
        object_repr=f'Usuario: {user.email if user else "Desconocido"}',
    )


@receiver(user_login_failed)
def on_user_login_failed(sender, credentials, request, **kwargs):
    from .models import AuditLog
    attempted_email = credentials.get('email') or credentials.get('username', '')
    AuditLog.log(
        AuditLog.EVENT_LOGIN_FAILED,
        request=request,
        object_repr=f'Intento fallido: {attempted_email}',
        extra={'attempted_email': attempted_email},
    )


# ──────────────────────────────────────────────────────────────────────────────
# Signals de Productos
# ──────────────────────────────────────────────────────────────────────────────

@receiver(post_save, sender='products.Product')
def on_product_saved(sender, instance, created, **kwargs):
    from .models import AuditLog

    event = AuditLog.EVENT_PRODUCT_CREATED if created else AuditLog.EVENT_PRODUCT_UPDATED
    AuditLog.log(
        event,
        obj=instance,
        object_repr=f'Producto: {instance.name} (SKU: {instance.sku})',
        extra={
            'price': str(instance.price),
            'stock': instance.stock,
            'is_active': instance.is_active,
        },
    )
