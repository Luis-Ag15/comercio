import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import SiteSetting

logger = logging.getLogger(__name__)
User = get_user_model()

def get_admin_emails():
    """Obtiene la lista de correos a donde enviar alertas de nuevos pedidos"""
    admin_emails = []
    
    # 1. Email configurado en SiteSetting
    site_setting = SiteSetting.objects.first()
    if site_setting and site_setting.email:
        admin_emails.append(site_setting.email)
    
    # 2. Emails de superusuarios y administradores
    superusers = User.objects.filter(is_superuser=True, is_active=True).exclude(email='').values_list('email', flat=True)
    admin_emails.extend(list(superusers))
    
    # 3. Fallback a settings si no hay ninguno
    if not admin_emails:
        if getattr(settings, 'EMAIL_HOST_USER', None):
            admin_emails.append(settings.EMAIL_HOST_USER)
        elif getattr(settings, 'ADMINS', None):
            admin_emails.extend([email for _, email in settings.ADMINS])
            
    # Eliminar duplicados preservando el orden
    return list(dict.fromkeys(admin_emails))

def send_order_admin_notification(order, request=None):
    """Envía correo de alerta al administrador cuando se crea un pedido"""
    recipient_list = get_admin_emails()
    if not recipient_list:
        logger.warning(f"No hay destinatarios configurados para notificar el pedido #{order.id}")
        return False
    
    # Construir URL del admin
    admin_path = reverse('admin:orders_order_change', args=[order.id])
    if request:
        admin_url = request.build_absolute_uri(admin_path)
    else:
        admin_url = f"http://localhost:8000{admin_path}"
    
    context = {
        'order': order,
        'admin_url': admin_url,
    }
    
    subject = f"🛍️ [Nuevo Pedido #{order.id}] de {order.get_full_name()} (${order.total})"
    message_txt = render_to_string('orders/emails/admin_order_notification.txt', context)
    message_html = render_to_string('orders/emails/admin_order_notification.html', context)
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', 'noreply@mitienda.com'))
    
    try:
        send_mail(
            subject=subject,
            message=message_txt,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=message_html,
            fail_silently=False
        )
        logger.info(f"Notificación de pedido #{order.id} enviada exitosamente a administradores: {recipient_list}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar notificación de pedido #{order.id} al admin: {e}")
        return False

def send_order_customer_confirmation(order):
    """Envía correo de confirmación de compra al cliente"""
    if not order.email:
        return False
    
    context = {
        'order': order,
    }
    
    subject = f"Confirmación de tu pedido #{order.id}"
    message_txt = render_to_string('orders/emails/customer_order_confirmation.txt', context)
    message_html = render_to_string('orders/emails/customer_order_confirmation.html', context)
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', 'noreply@mitienda.com'))
    
    try:
        send_mail(
            subject=subject,
            message=message_txt,
            from_email=from_email,
            recipient_list=[order.email],
            html_message=message_html,
            fail_silently=False
        )
        logger.info(f"Confirmación de pedido #{order.id} enviada al cliente: {order.email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar confirmación de pedido #{order.id} al cliente: {e}")
        return False
