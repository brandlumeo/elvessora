from django import template
from django.urls import reverse

from core.models import SiteSettings
from orders.models import Order
from products.models import ProductVariant

register = template.Library()


@register.simple_tag
def admin_alert_count():
    """Pending orders + low-stock variants — shown as the sidebar's bell badge."""
    threshold = SiteSettings.get().low_stock_threshold
    pending = Order.objects.filter(status__in=['pending', 'confirmed', 'processing']).count()
    low_stock = ProductVariant.objects.filter(stock_quantity__lte=threshold).count()
    return pending + low_stock


@register.simple_tag
def admin_alert_items(limit=6):
    """Pending orders + low-stock variants for the notification bell dropdown."""
    threshold = SiteSettings.get().low_stock_threshold
    items = []

    for order in Order.objects.filter(
        status__in=['pending', 'confirmed', 'processing']
    ).order_by('-created_at')[:limit]:
        items.append({
            'icon': 'bi-bag-check',
            'title': f'Order #{order.order_number}',
            'subtitle': f'{order.get_status_display()} — {order.shipping_name}',
            'url': reverse('admin:orders_order_change', args=[order.pk]),
        })

    for variant in ProductVariant.objects.filter(
        stock_quantity__lte=threshold
    ).select_related('product').order_by('stock_quantity')[:limit]:
        items.append({
            'icon': 'bi-exclamation-triangle',
            'title': f'{variant.product.name} ({variant.get_size_display()})',
            'subtitle': f'Low stock — {variant.stock_quantity} left',
            'url': reverse('admin:products_product_change', args=[variant.product_id]),
        })

    return items[:limit]
