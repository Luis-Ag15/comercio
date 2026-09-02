from django import forms
from .models import Order

class OrderCreateForm(forms.ModelForm):
    """Formulario para captura de datos de envío en el checkout"""
    class Meta:
        model = Order
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'address',
            'city',
            'state',
            'country',
            'postal_code',
            'payment_method',
            'order_notes',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+52 55 1234 5678'}),
            'address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle y número exterior / interior'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Colonia'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Municipio'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado / Provincia'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código Postal'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'order_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Instrucciones especiales para la entrega o referencias del domicilio (opcional)...'
            }),
        }
