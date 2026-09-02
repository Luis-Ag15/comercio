from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0
    readonly_fields = ('product_name', 'product_sku', 'price', 'quantity', 'get_cost_display')
    fields = ('product', 'product_name', 'product_sku', 'price', 'quantity', 'get_cost_display')
    
    def get_cost_display(self, obj):
        return f"${obj.get_cost():.2f}"
    get_cost_display.short_description = 'Subtotal'

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_info',
        'status',
        'payment_status',
        'payment_method',
        'total_display',
        'items_count',
        'created_at'
    )
    list_display_links = ('id', 'customer_info')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at', 'updated_at')
    search_fields = ('id', 'first_name', 'last_name', 'email', 'phone', 'address', 'city', 'tracking_number')
    list_editable = ('status', 'payment_status')
    readonly_fields = ('created_at', 'updated_at', 'subtotal', 'discount', 'shipping_cost', 'total')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Información General', {
            'fields': ('user', 'status', 'payment_status', 'payment_method', 'tracking_number')
        }),
        ('Datos del Cliente y Envío', {
            'fields': (
                ('first_name', 'last_name'),
                ('email', 'phone'),
                'address',
                ('city', 'state', 'postal_code'),
                'country',
                'order_notes'
            )
        }),
        ('Totales e Importes', {
            'fields': ('subtotal', 'discount', 'shipping_cost', 'total')
        }),
        ('Fechas de Auditoría', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def customer_info(self, obj):
        return format_html(
            "<strong>{}</strong><br><small class='text-muted'>{} | Tel: {}</small>",
            obj.get_full_name(),
            obj.email,
            obj.phone
        )
    customer_info.short_description = 'Cliente'
    
    def total_display(self, obj):
        return format_html("<strong>${}</strong>", f"{obj.total:.2f}")
    total_display.short_description = 'Total'
    
    def items_count(self, obj):
        return obj.get_items_count()
    items_count.short_description = 'Items'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'processing': '#0dcaf0',
            'shipped': '#0d6efd',
            'delivered': '#198754',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: #000; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'paid': '#198754',
            'failed': '#dc3545',
            'refunded': '#6c757d',
        }
        color = colors.get(obj.payment_status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Pago'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product_name', 'product_sku', 'price', 'quantity', 'get_cost')
    search_fields = ('order__id', 'product_name', 'product_sku')
    list_filter = ('order__created_at',)
    readonly_fields = ('order', 'product', 'product_name', 'product_sku', 'price', 'quantity')
