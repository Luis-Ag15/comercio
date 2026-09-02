from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType

class SiteSetting(models.Model):
    """Configuraciones del sitio web"""
    site_name = models.CharField('Nombre del sitio', max_length=100, default='Mi Tienda')
    site_description = models.TextField('Descripción', max_length=500, blank=True)
    logo = models.ImageField('Logo', upload_to='settings/', blank=True, null=True)
    favicon = models.ImageField('Favicon', upload_to='settings/', blank=True, null=True)
    
    # Contacto
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Teléfono', max_length=20, blank=True)
    address = models.TextField('Dirección', blank=True)
    
    # Redes sociales
    facebook = models.URLField('Facebook', blank=True)
    instagram = models.URLField('Instagram', blank=True)
    twitter = models.URLField('Twitter', blank=True)
    youtube = models.URLField('YouTube', blank=True)
    
    # SEO
    meta_title = models.CharField('Meta título', max_length=100, blank=True)
    meta_description = models.TextField('Meta descripción', max_length=500, blank=True)
    meta_keywords = models.CharField('Meta keywords', max_length=255, blank=True)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Configuración del sitio'
        verbose_name_plural = 'Configuraciones del sitio'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Asegura que solo exista un registro
        if not self.pk and SiteSetting.objects.exists():
            return
        super().save(*args, **kwargs)


# ──────────────────────────────────────────────────────────────────────────────
# Bitácora de Auditoría
# ──────────────────────────────────────────────────────────────────────────────

class AuditLog(models.Model):
    """
    Registro inmutable de acciones relevantes del sistema.
    Los registros NO deben modificarse ni eliminarse; solo se crean.
    """

    # ── Tipos de evento ────────────────────────────────────────────────────────
    EVENT_LOGIN_SUCCESS  = 'login_success'
    EVENT_LOGIN_FAILED   = 'login_failed'
    EVENT_LOGOUT         = 'logout'
    EVENT_ORDER_CREATED  = 'order_created'
    EVENT_ORDER_UPDATED  = 'order_updated'
    EVENT_PRODUCT_CREATED = 'product_created'
    EVENT_PRODUCT_UPDATED = 'product_updated'
    EVENT_STOCK_ADJUSTED = 'stock_adjusted'

    EVENT_TYPE_CHOICES = [
        (EVENT_LOGIN_SUCCESS,  'Inicio de sesión exitoso'),
        (EVENT_LOGIN_FAILED,   'Intento de login fallido'),
        (EVENT_LOGOUT,         'Cierre de sesión'),
        (EVENT_ORDER_CREATED,  'Pedido creado'),
        (EVENT_ORDER_UPDATED,  'Pedido actualizado'),
        (EVENT_PRODUCT_CREATED,'Producto creado'),
        (EVENT_PRODUCT_UPDATED,'Producto modificado'),
        (EVENT_STOCK_ADJUSTED, 'Inventario ajustado'),
    ]

    # ── Campos ─────────────────────────────────────────────────────────────────
    timestamp = models.DateTimeField('Fecha y hora', auto_now_add=True, db_index=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuario',
    )

    ip_address = models.GenericIPAddressField(
        'Dirección IP', null=True, blank=True
    )

    event_type = models.CharField(
        'Tipo de evento', max_length=40,
        choices=EVENT_TYPE_CHOICES, db_index=True
    )

    object_repr = models.CharField(
        'Objeto afectado', max_length=255, blank=True,
        help_text='Representación legible del objeto (ej. "Pedido #42")'
    )

    object_id = models.PositiveBigIntegerField(
        'ID del objeto', null=True, blank=True
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Tipo de modelo',
    )

    changes = models.JSONField(
        'Cambios', default=dict, blank=True,
        help_text='Valores anteriores y nuevos en formato {"campo": {"before": ..., "after": ...}}'
    )

    extra = models.JSONField(
        'Información extra', default=dict, blank=True,
        help_text='Datos adicionales de contexto (request path, agente, etc.)'
    )

    class Meta:
        verbose_name = 'Registro de auditoría'
        verbose_name_plural = 'Bitácora de auditoría'
        ordering = ['-timestamp']
        # Tabla de solo lectura — ningún admin debería poder borrar/editar
        default_permissions = ('view',)

    def __str__(self):
        user_str = self.user.email if self.user else 'Anónimo'
        return f"[{self.get_event_type_display()}] {user_str} — {self.timestamp:%Y-%m-%d %H:%M:%S}"

    # ── Factory helper ─────────────────────────────────────────────────────────
    @classmethod
    def log(
        cls,
        event_type: str,
        *,
        user=None,
        request=None,
        obj=None,
        object_repr: str = '',
        changes: dict = None,
        extra: dict = None,
    ) -> 'AuditLog':
        """
        Crea un registro de auditoría de manera conveniente.

        Args:
            event_type: Constante de evento (ej. AuditLog.EVENT_ORDER_CREATED).
            user: Instancia del usuario que realizó la acción (opcional).
            request: HttpRequest para extraer IP y metadata (opcional).
            obj: Instancia del modelo Django afectado (opcional).
            object_repr: Texto legible del objeto si no se pasa `obj`.
            changes: Dict {"campo": {"before": x, "after": y}}.
            extra: Dict con datos adicionales de contexto.
        """
        ip = None
        extra_data = extra or {}

        if request is not None:
            ip = _get_client_ip(request)
            extra_data.setdefault('path', request.path)
            extra_data.setdefault('method', request.method)
            if not user and request.user.is_authenticated:
                user = request.user

        ct = None
        oid = None
        repr_str = object_repr

        if obj is not None:
            try:
                ct = ContentType.objects.get_for_model(obj)
                oid = obj.pk
            except Exception:
                pass
            if not repr_str:
                repr_str = str(obj)

        return cls.objects.create(
            event_type=event_type,
            user=user,
            ip_address=ip,
            content_type=ct,
            object_id=oid,
            object_repr=repr_str,
            changes=changes or {},
            extra=extra_data,
        )


def _get_client_ip(request) -> str:
    """Extrae la IP real del cliente teniendo en cuenta proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')

