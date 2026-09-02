from .models import SiteSetting

def site_settings(request):
    """Procesador de contexto para configuraciones del sitio"""
    try:
        settings = SiteSetting.objects.first()
    except:
        settings = None
    
    return {
        'site_settings': settings,
        'site_name': settings.site_name if settings else 'Mi Tienda',
    }