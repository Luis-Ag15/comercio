from django.contrib import admin
from .models import SiteSetting, AuditLog

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Información General', {
            'fields': ('site_name', 'site_description', 'logo', 'favicon')
        }),
        ('Contacto', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Redes Sociales', {
            'fields': ('facebook', 'instagram', 'twitter', 'youtube')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
    )
    list_display = ('site_name', 'email', 'phone')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Vista de solo lectura de la bitácora de auditoría."""

    list_display = (
        'timestamp', 'event_type_badge', 'user', 'ip_address',
        'object_repr',
    )
    list_filter = ('event_type', 'timestamp')
    search_fields = ('user__email', 'ip_address', 'object_repr', 'extra')
    readonly_fields = (
        'timestamp', 'user', 'ip_address', 'event_type',
        'object_repr', 'object_id', 'content_type',
        'changes_pretty', 'extra_pretty',
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Evento', {
            'fields': ('timestamp', 'event_type', 'user', 'ip_address')
        }),
        ('Objeto afectado', {
            'fields': ('object_repr', 'content_type', 'object_id')
        }),
        ('Detalle del cambio', {
            'fields': ('changes_pretty',),
        }),
        ('Contexto adicional', {
            'fields': ('extra_pretty',),
            'classes': ('collapse',),
        }),
    )

    # ── Deshabilitar toda escritura ────────────────────────────────────────────
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    # ── Columnas personalizadas ────────────────────────────────────────────────
    def event_type_badge(self, obj):
        from django.utils.html import format_html
        color_map = {
            AuditLog.EVENT_LOGIN_SUCCESS:   '#28a745',
            AuditLog.EVENT_LOGIN_FAILED:    '#dc3545',
            AuditLog.EVENT_LOGOUT:          '#6c757d',
            AuditLog.EVENT_ORDER_CREATED:   '#007bff',
            AuditLog.EVENT_ORDER_UPDATED:   '#fd7e14',
            AuditLog.EVENT_PRODUCT_CREATED: '#20c997',
            AuditLog.EVENT_PRODUCT_UPDATED: '#17a2b8',
            AuditLog.EVENT_STOCK_ADJUSTED:  '#ffc107',
        }
        color = color_map.get(obj.event_type, '#6c757d')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;'
            'border-radius:4px;font-size:0.8em;font-weight:bold">{}</span>',
            color, obj.get_event_type_display()
        )
    event_type_badge.short_description = 'Evento'

    def changes_pretty(self, obj):
        import json
        from django.utils.html import format_html
        if not obj.changes:
            return '—'
        return format_html('<pre style="margin:0;font-size:0.85em">{}</pre>',
                           json.dumps(obj.changes, ensure_ascii=False, indent=2))
    changes_pretty.short_description = 'Cambios (antes → después)'

    def extra_pretty(self, obj):
        import json
        from django.utils.html import format_html
        if not obj.extra:
            return '—'
        return format_html('<pre style="margin:0;font-size:0.85em">{}</pre>',
                           json.dumps(obj.extra, ensure_ascii=False, indent=2))
    extra_pretty.short_description = 'Información extra'