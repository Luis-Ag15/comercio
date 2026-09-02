from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from ckeditor.fields import RichTextField

class Category(models.Model):
    """Categoría de productos"""
    name = models.CharField('Nombre', max_length=100)
    slug = models.SlugField('Slug', max_length=120, unique=True)
    description = models.TextField('Descripción', max_length=500, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='Categoría padre'
    )
    image = models.ImageField('Imagen', upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField('Activo', default=True)
    order = models.PositiveIntegerField('Orden', default=0)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category_detail', kwargs={'slug': self.slug})

class Brand(models.Model):
    """Marca del producto"""
    name = models.CharField('Nombre', max_length=100)
    slug = models.SlugField('Slug', max_length=120, unique=True)
    logo = models.ImageField('Logo', upload_to='brands/', blank=True, null=True)
    description = models.TextField('Descripción', max_length=500, blank=True)
    is_active = models.BooleanField('Activo', default=True)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    """Modelo de producto"""
    CATEGORY_CHOICES = (
        ('new', 'Nuevo'),
        ('featured', 'Destacado'),
        ('sale', 'Oferta'),
        ('normal', 'Normal'),
    )
    
    name = models.CharField('Nombre', max_length=200)
    slug = models.SlugField('Slug', max_length=220, unique=True)
    sku = models.CharField('SKU', max_length=50, unique=True)
    description = RichTextField('Descripción')
    short_description = models.TextField('Descripción corta', max_length=300, blank=True)
    
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Categoría'
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name='Marca'
    )
    
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    discount_price = models.DecimalField('Precio de oferta', max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField('Stock', default=0)
    min_stock = models.PositiveIntegerField('Stock mínimo', default=0)
    
    main_image = models.ImageField('Imagen principal', upload_to='products/')
    images = models.ManyToManyField('ProductImage', blank=True, related_name='products')
    
    tags = models.CharField('Etiquetas', max_length=255, blank=True, help_text='Separar con comas')
    
    is_active = models.BooleanField('Activo', default=True)
    is_featured = models.BooleanField('Destacado', default=False)
    is_new = models.BooleanField('Nuevo', default=False)
    is_on_sale = models.BooleanField('En oferta', default=False)
    product_type = models.CharField('Tipo', max_length=20, choices=CATEGORY_CHOICES, default='normal')
    
    weight = models.DecimalField('Peso (kg)', max_digits=6, decimal_places=2, blank=True, null=True)
    dimensions = models.CharField('Dimensiones', max_length=100, blank=True)
    material = models.CharField('Material', max_length=100, blank=True)
    
    views = models.PositiveIntegerField('Vistas', default=0)
    sales = models.PositiveIntegerField('Ventas', default=0)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})
    
    def get_price(self):
        """Retorna el precio de oferta si existe"""
        return self.discount_price if self.discount_price else self.price
    
    def get_discount_percentage(self):
        """Calcula el porcentaje de descuento"""
        if self.discount_price:
            return int(((self.price - self.discount_price) / self.price) * 100)
        return 0
    
    def is_in_stock(self):
        return self.stock > 0
    
    @property
    def average_rating(self):
        """Calcula la calificación promedio"""
        reviews = self.reviews.all()
        if reviews.exists():
            return sum([r.rating for r in reviews]) / reviews.count()
        return 0
    
    @property
    def reviews_count(self):
        return self.reviews.count()

class ProductImage(models.Model):
    """Imágenes adicionales del producto"""
    image = models.ImageField('Imagen', upload_to='products/gallery/')
    alt_text = models.CharField('Texto alternativo', max_length=200, blank=True)
    is_main = models.BooleanField('Imagen principal', default=False)
    order = models.PositiveIntegerField('Orden', default=0)
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Imagen del producto'
        verbose_name_plural = 'Imágenes del producto'
        ordering = ['order']
    
    def __str__(self):
        return f"Imagen {self.id}"

class ProductVariant(models.Model):
    """Variantes del producto (talla, color, etc.)"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField('Nombre de la variante', max_length=100)
    sku = models.CharField('SKU', max_length=50, unique=True)
    price_adjustment = models.DecimalField('Ajuste de precio', max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField('Stock', default=0)
    image = models.ImageField('Imagen', upload_to='products/variants/', blank=True, null=True)
    is_active = models.BooleanField('Activo', default=True)
    
    class Meta:
        verbose_name = 'Variante del producto'
        verbose_name_plural = 'Variantes del producto'
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"

class Review(models.Model):
    """Reseña de producto por un usuario"""
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Producto'
    )
    author_name = models.CharField('Nombre', max_length=100)
    author_email = models.EmailField('Email', blank=True)
    rating = models.PositiveSmallIntegerField('Calificación', choices=RATING_CHOICES, default=5)
    title = models.CharField('Título', max_length=200, blank=True)
    body = models.TextField('Comentario')
    is_approved = models.BooleanField('Aprobado', default=False)
    created_at = models.DateTimeField('Creado', auto_now_add=True)

    class Meta:
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author_name} – {self.product.name} ({self.rating}★)"