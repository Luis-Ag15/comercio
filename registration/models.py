from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from core.encryption import EncryptedCharField

class User(AbstractUser):
    """Modelo de usuario personalizado"""
    email = models.EmailField(_('email address'), unique=True)
    phone = EncryptedCharField('Teléfono', blank=True, default='')
    is_verified = models.BooleanField('Verificado', default=False)
    verification_token = models.CharField('Token de verificación', max_length=100, blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

class Profile(models.Model):
    """Perfil de usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField('Avatar', upload_to='profiles/', blank=True, null=True)
    bio = models.TextField('Biografía', max_length=500, blank=True)
    birth_date = models.DateField('Fecha de nacimiento', blank=True, null=True)
    
    # Direcciones — cifradas en la BD
    street = EncryptedCharField('Calle', blank=True, default='')
    city = EncryptedCharField('Ciudad', blank=True, default='')
    state = EncryptedCharField('Estado', blank=True, default='')
    country = EncryptedCharField('País', blank=True, default='')
    postal_code = EncryptedCharField('Código postal', blank=True, default='')
    
    # Preferencias
    newsletter = models.BooleanField('Recibir newsletter', default=True)
    
    created_at = models.DateTimeField('Creado', auto_now_add=True)
    updated_at = models.DateTimeField('Actualizado', auto_now=True)
    
    class Meta:
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
    
    def __str__(self):
        return f"Perfil de {self.user.email}"