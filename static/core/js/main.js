// Main JavaScript file for the e-commerce site

$(document).ready(function() {
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow', function() {
            $(this).remove();
        });
    }, 5000);

    // Handle quantity input changes in cart
    $('.quantity-input').on('change', function() {
        const form = $(this).closest('form');
        form.submit();
    });

    // Handle add to cart via AJAX
    $('.add-to-cart-form').on('submit', function(e) {
        e.preventDefault();
        const form = $(this);
        const url = form.attr('action');
        const data = form.serialize();

        $.ajax({
            url: url,
            method: 'POST',
            data: data,
            success: function(response) {
                if (response.success) {
                    showToast(response.message, 'success');
                    updateCartBadge(response.cart_total);
                }
            },
            error: function(xhr) {
                showToast('Error al agregar al carrito', 'danger');
            }
        });
    });

    // Toast notifications
    function showToast(message, type = 'success') {
        const toastHtml = `
            <div class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        const toastContainer = $('#toast-container');
        if (toastContainer.length === 0) {
            $('body').append('<div id="toast-container" class="position-fixed bottom-0 end-0 p-3" style="z-index: 1050;"></div>');
        }

        const toast = $(toastHtml);
        $('#toast-container').append(toast);
        const bsToast = new bootstrap.Toast(toast[0]);
        bsToast.show();

        // Auto-remove after 5 seconds
        setTimeout(function() {
            toast.remove();
        }, 5000);
    }

    // Update cart badge
    function updateCartBadge(count) {
        const badge = $('.cart-badge');
        if (badge.length) {
            badge.text(count);
            if (count > 0) {
                badge.show();
            } else {
                badge.hide();
            }
        }
    }

    // Product image gallery
    $('.product-thumbnail').on('click', function() {
        const mainImage = $('#main-product-image');
        if (mainImage.length) {
            const newSrc = $(this).data('image') || $(this).attr('src');
            mainImage.attr('src', newSrc);
            $(this).addClass('active').siblings().removeClass('active');
        }
    });

    // Search form auto-submit on category change
    $('#search-category').on('change', function() {
        $('#search-form').submit();
    });

    // Sort select auto-submit
    $('#sort-select').on('change', function() {
        const url = new URL(window.location.href);
        url.searchParams.set('sort', $(this).val());
        window.location.href = url.toString();
    });

    // Price range slider
    const priceSlider = document.getElementById('price-range');
    if (priceSlider) {
        noUiSlider.create(priceSlider, {
            start: [0, 1000],
            connect: true,
            range: {
                'min': 0,
                'max': 1000
            }
        });

        priceSlider.noUiSlider.on('update', function(values) {
            const min = Math.round(values[0]);
            const max = Math.round(values[1]);
            $('#min-price').val(min);
            $('#max-price').val(max);
            $('#price-range-display').text(`$${min} - $${max}`);
        });
    }

    // Cart item quantity increase/decrease
    $('.qty-btn').on('click', function() {
        const input = $(this).siblings('.quantity-input');
        let currentVal = parseInt(input.val());
        
        if ($(this).data('action') === 'increase') {
            input.val(currentVal + 1);
        } else if ($(this).data('action') === 'decrease' && currentVal > 1) {
            input.val(currentVal - 1);
        }
        
        input.trigger('change');
    });

    // Confirm delete actions
    $('.confirm-delete').on('click', function(e) {
        if (!confirm('¿Estás seguro de que deseas eliminar este elemento?')) {
            e.preventDefault();
        }
    });

    // Image lazy loading
    if ('IntersectionObserver' in window) {
        const images = document.querySelectorAll('img[data-src]');
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    imageObserver.unobserve(img);
                }
            });
        });

        images.forEach(img => imageObserver.observe(img));
    }

    // Mobile menu toggle enhancement
    $('.navbar-toggler').on('click', function() {
        $(this).toggleClass('active');
    });

    // Smooth scroll to top
    $('.scroll-top').on('click', function(e) {
        e.preventDefault();
        $('html, body').animate({ scrollTop: 0 }, 500);
    });

    // Show/hide scroll to top button
    $(window).on('scroll', function() {
        const scrollTop = $(window).scrollTop();
        if (scrollTop > 300) {
            $('.scroll-top').fadeIn();
        } else {
            $('.scroll-top').fadeOut();
        }
    });
});

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}