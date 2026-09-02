from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Profile
from datetime import date
import re

class UserRegistrationForm(UserCreationForm):
    """Formulario de registro de usuario"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    username = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'})
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'})
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[\w.@+-]+$', username):
            raise ValidationError('El nombre de usuario contiene caracteres no válidos.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email ya está registrado.')
        return email

class UserLoginForm(AuthenticationForm):
    """Formulario de inicio de sesión"""
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'})
    )
    
    class Meta:
        fields = ['username', 'password']

class ProfileUpdateForm(forms.ModelForm):
    """Formulario de actualización de perfil"""
    phone = forms.CharField(
        label='Teléfono',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+52 55 1234 5678'})
    )

    class Meta:
        model = Profile
        fields = ['avatar', 'street', 'city', 'state', 
                 'country', 'postal_code', 'newsletter']
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'street': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Calle y número exterior / interior'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Colonia'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Municipio'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Estado / Provincia'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código postal'}),
            'newsletter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['phone'].initial = self.instance.user.phone

    def save(self, commit=True):
        profile = super().save(commit=commit)
        if 'phone' in self.cleaned_data and profile.user:
            profile.user.phone = self.cleaned_data['phone']
            profile.user.save(update_fields=['phone'])
        return profile
    
    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar:
            # Validar tamaño de archivo (máximo 5MB)
            if avatar.size > 5 * 1024 * 1024:
                raise ValidationError('El archivo no puede ser mayor a 5MB.')
            
            # Validar tipo de archivo
            valid_types = ['image/jpeg', 'image/png', 'image/gif']
            if hasattr(avatar, 'content_type') and avatar.content_type not in valid_types:
                raise ValidationError('Solo se permiten imágenes JPEG, PNG o GIF.')
        return avatar