from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Brand, Product, ProductImage, ProductVariant

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'is_active', 'order')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['order', 'name']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'price', 'discount_price', 'stock', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'is_new', 'is_on_sale', 'category', 'brand')
    search_fields = ('name', 'sku', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('views', 'sales', 'created_at', 'updated_at')
    list_editable = ('price', 'discount_price', 'stock', 'is_active', 'is_featured')
    inlines = [ProductVariantInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'slug', 'sku', 'description', 'short_description')
        }),
        ('Categorías', {
            'fields': ('category', 'brand', 'tags')
        }),
        ('Precios y Stock', {
            'fields': ('price', 'discount_price', 'stock', 'min_stock')
        }),
        ('Imágenes', {
            'fields': ('main_image',)
        }),
        ('Estado', {
            'fields': ('is_active', 'is_featured', 'is_new', 'is_on_sale', 'product_type')
        }),
        ('Detalles adicionales', {
            'fields': ('weight', 'dimensions', 'material')
        }),
        ('Estadísticas', {
            'fields': ('views', 'sales', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.main_image:
            return format_html('<img src="{}" width="100" height="100" style="object-fit:cover"/>', obj.main_image.url)
        return 'No image'
    image_preview.short_description = 'Vista previa'

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'alt_text', 'is_main', 'order')
    list_filter = ('is_main',)
    list_editable = ('is_main', 'order')

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'sku', 'price_adjustment', 'stock', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'sku', 'product__name')