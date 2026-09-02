from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from products.models import Product, Category, Brand

class HomeView(TemplateView):
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured products (or fallback to deals/popular if none explicitly flagged)
        featured = Product.objects.filter(is_active=True, is_featured=True)[:8]
        if not featured.exists():
            featured = Product.objects.filter(is_active=True).order_by('-discount_price', '-views', '-created_at')[:8]
            
        context['featured_products'] = featured
        context['latest_products'] = Product.objects.filter(
            is_active=True
        ).order_by('-created_at')[:8]
        context['categories'] = Category.objects.filter(is_active=True)[:6]
        context['brands'] = Brand.objects.filter(is_active=True)[:8]
        
        # Highlight product for hero section (prefer discounted or featured or latest)
        hero_candidate = Product.objects.filter(is_active=True, discount_price__isnull=False).first()
        if not hero_candidate:
            hero_candidate = Product.objects.filter(is_active=True).first()
        context['hero_product'] = hero_candidate
        
        return context

class AboutView(TemplateView):
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Sobre Nosotros'
        return context

class ContactView(TemplateView):
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Contacto'
        return context

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()
        
        if name and email and message:
            messages.success(
                request,
                '¡Gracias por comunicarte con nosotros! Hemos recibido tu mensaje y nos pondremos en contacto contigo a la brevedad.'
            )
            return redirect('core:contact')
        else:
            messages.error(request, 'Por favor completa todos los campos requeridos.')
            return self.get(request, *args, **kwargs)


class TermsView(TemplateView):
    template_name = 'core/terms.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Términos y Condiciones'
        return context


class PrivacyView(TemplateView):
    template_name = 'core/privacy.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Política de Privacidad'
        return context
