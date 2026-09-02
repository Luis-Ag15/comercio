from django import forms
from .models import Product, Category, Brand


class ProductForm(forms.ModelForm):
    """Formulario para crear y editar productos desde el frontend."""

    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'brand',
            'short_description', 'description',
            'price', 'discount_price',
            'stock', 'min_stock',
            'main_image',
            'tags',
            'weight', 'dimensions', 'material',
            'product_type',
            'is_active', 'is_featured', 'is_new', 'is_on_sale',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del producto',
            }),
            'sku': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. PROD-001',
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Descripción breve (máx. 300 caracteres)',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Descripción detallada del producto...',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0',
            }),
            'discount_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00 (opcional)',
                'step': '0.01',
                'min': '0',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
            }),
            'min_stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
            }),
            'main_image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'main_image_input',
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'tag1, tag2, tag3',
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Kg (opcional)',
                'step': '0.01',
            }),
            'dimensions': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 30x20x10 cm',
            }),
            'material': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Algodón, Plástico...',
            }),
            'product_type': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_new': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_on_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # Sobreescribir description como CharField puro para evitar
    # conflictos con RichTextField/CKEditor en el formulario frontend.
    description = forms.CharField(
        label='Descripción completa',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Descripción detallada del producto...',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['brand'].required = False
        self.fields['discount_price'].required = False
        self.fields['weight'].required = False
        self.fields['dimensions'].required = False
        self.fields['material'].required = False
        self.fields['tags'].required = False
        self.fields['short_description'].required = False
        # Garantizar que is_active siempre inicia como True en formularios nuevos
        if not self.instance or not self.instance.pk:
            self.fields['is_active'].initial = True
            self.fields['is_featured'].initial = False
            self.fields['is_new'].initial = False
            self.fields['is_on_sale'].initial = False
        # Solo categorías y marcas activas
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['brand'].queryset = Brand.objects.filter(is_active=True)
        self.fields['brand'].empty_label = '— Sin marca —'


class CategoryForm(forms.ModelForm):
    """Formulario para crear y editar categorías desde el frontend."""

    class Meta:
        model = Category
        fields = ['name', 'description', 'parent', 'image', 'is_active', 'order']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción breve (opcional)',
            }),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'cat_image_input',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['parent'].required = False
        self.fields['image'].required = False
        self.fields['parent'].empty_label = '— Sin categoría padre —'
        # Evitar que una categoría sea su propio padre
        if self.instance and self.instance.pk:
            self.fields['parent'].queryset = Category.objects.exclude(pk=self.instance.pk)
        else:
            self.fields['parent'].queryset = Category.objects.all()


class BrandForm(forms.ModelForm):
    """Formulario para crear y editar marcas desde el frontend."""

    class Meta:
        model = Brand
        fields = ['name', 'description', 'logo', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la marca',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción breve (opcional)',
            }),
            'logo': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'brand_logo_input',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['description'].required = False
        self.fields['logo'].required = False
