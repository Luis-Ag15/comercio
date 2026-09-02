from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil'

class CustomUserAdmin(UserAdmin):
    """Admin personalizado para el modelo User"""
    inlines = [ProfileInline]
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_verified', 'is_active')
    list_filter = ('is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Información adicional', {
            'fields': ('phone', 'is_verified', 'verification_token')
        }),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
