from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from .forms import UserRegistrationForm, UserLoginForm, ProfileUpdateForm
from .models import User, Profile

class RegisterView(CreateView):
    """Vista de registro de usuarios"""
    model = User
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # Generar token de verificación
        user.verification_token = get_random_string(50)
        user.save()
        
        # Enviar email de verificación
        self.send_verification_email(user)
        
        messages.success(self.request, 'Registro exitoso. Revisa tu email para verificar tu cuenta.')
        return response
    
    def send_verification_email(self, user):
        """Envía email de verificación"""
        verification_url = self.request.build_absolute_uri(
            reverse('registration:verify_email', kwargs={'token': user.verification_token})
        )
        
        subject = 'Verifica tu cuenta - Mi Tienda'
        message = f"""
        Hola {user.first_name},
        
        Gracias por registrarte. Por favor, haz clic en el siguiente enlace para verificar tu cuenta:
        
        {verification_url}
        
        Si no solicitaste este registro, ignora este mensaje.
        
        Saludos,
        El equipo de Mi Tienda
        """
        
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=True,
        )
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{field}: {error}')
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse('registration:login')

class CustomLoginView(LoginView):
    """Vista personalizada de inicio de sesión"""
    form_class = UserLoginForm
    template_name = 'registration/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import site_settings
        context.update(site_settings(self.request))
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.get_user()
        
        # Verificar si el usuario está verificado
        if not user.is_verified:
            messages.warning(self.request, 'Por favor, verifica tu cuenta antes de iniciar sesión.')
            logout(self.request)
            return redirect('registration:login')
        
        user_name = user.first_name or user.username
        messages.success(self.request, f'¡Bienvenido de nuevo, {user_name}!')
        return response

def verify_email(request, token):
    """Verifica el email del usuario"""
    user = get_object_or_404(User, verification_token=token)
    
    if user.is_verified:
        messages.info(request, 'Tu cuenta ya estaba verificada.')
    else:
        user.is_verified = True
        user.verification_token = None
        user.save()
        messages.success(request, '¡Cuenta verificada exitosamente! Ahora puedes iniciar sesión.')
    
    return redirect('registration:login')

@login_required
def profile_view(request):
    """Vista del perfil de usuario"""
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente.')
            return redirect('registration:profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    context = {
        'user': user,
        'profile': profile,
        'form': form,
    }
    return render(request, 'registration/profile.html', context)

@login_required
def logout_view(request):
    """Cierra sesión del usuario"""
    logout(request)
    messages.info(request, 'Sesión cerrada exitosamente.')
    return redirect('core:home')


class CustomPasswordResetView(auth_views.PasswordResetView):
    """Vista para solicitar restablecimiento de contraseña"""
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('registration:password_reset_done')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import site_settings
        context.update(site_settings(self.request))
        return context

    def form_valid(self, form):
        from core.context_processors import site_settings
        settings_ctx = site_settings(self.request)
        opts = {
            'use_https': self.request.is_secure(),
            'token_generator': self.token_generator,
            'from_email': self.from_email,
            'email_template_name': self.email_template_name,
            'subject_template_name': self.subject_template_name,
            'request': self.request,
            'html_email_template_name': self.html_email_template_name,
            'extra_email_context': {'site_name': settings_ctx.get('site_name', 'Mi Tienda')},
        }
        form.save(**opts)
        return super(auth_views.PasswordResetView, self).form_valid(form)


class CustomPasswordResetDoneView(auth_views.PasswordResetDoneView):
    """Vista informativa tras enviar correo de restablecimiento"""
    template_name = 'registration/password_reset_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import site_settings
        context.update(site_settings(self.request))
        return context


class CustomPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Vista para introducir la nueva contraseña"""
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('registration:password_reset_complete')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import site_settings
        context.update(site_settings(self.request))
        return context


class CustomPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    """Vista de confirmación de contraseña restablecida"""
    template_name = 'registration/password_reset_complete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from core.context_processors import site_settings
        context.update(site_settings(self.request))
        return context

