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


# (app_label, object_name) -> (bootstrap icon class, short description)
MODEL_META = {
    ('orders', 'Order'): ('bi-bag-check', 'Customer orders, statuses, and shipping details.'),
    ('orders', 'Coupon'): ('bi-tag', 'Discount codes customers can apply at checkout.'),
    ('orders', 'Payment'): ('bi-credit-card', 'Payment records for orders.'),
    ('orders', 'Refund'): ('bi-arrow-counterclockwise', 'Refunds issued against orders.'),
    ('products', 'Product'): ('bi-droplet', 'Your perfumes — pricing, notes, images, and variants.'),
    ('products', 'Collection'): ('bi-collection', 'Curated product groupings shown on the site.'),
    ('products', 'Category'): ('bi-folder', 'Top-level product categories.'),
    ('products', 'Brand'): ('bi-award', 'Brand records linked to products.'),
    ('products', 'FragranceFamily'): ('bi-flower1', 'Scent family tags (Woody, Floral, Citrus, etc.).'),
    ('products', 'Occasion'): ('bi-calendar-event', 'Occasion tags (Daily, Office, Wedding, etc.).'),
    ('products', 'GiftSet'): ('bi-gift', 'Bundled gift sets combining multiple products.'),
    ('accounts', 'Customer'): ('bi-people', 'Registered storefront customers.'),
    ('accounts', 'Address'): ('bi-geo-alt', 'Saved shipping addresses.'),
    ('reviews', 'Review'): ('bi-star', 'Customer product reviews and ratings.'),
    ('inventory', 'Inventory'): ('bi-boxes', 'Stock levels per product variant.'),
    ('core', 'FAQ'): ('bi-question-circle', 'Frequently asked questions shown on the FAQ page.'),
    ('core', 'LegalPage'): ('bi-file-earmark-text', 'Privacy Policy, Terms, Shipping, Returns, and other legal pages.'),
    ('core', 'HomePageContent'): ('bi-house', 'Editable text/images for the homepage’s built-in sections.'),
    ('core', 'HomePageHighlight'): ('bi-stars', 'Small highlight items (hero features, ingredients, value props).'),
    ('core', 'SiteSettings'): ('bi-gear', 'Global store settings — brand info, contact details, thresholds.'),
    ('auth', 'User'): ('bi-shield-lock', 'Admin/staff accounts and their permissions.'),
    ('auth', 'Group'): ('bi-people-fill', 'Reusable permission bundles you can assign to staff accounts.'),
}

DEFAULT_ICON = 'bi-folder2'


def _model_app_label(model):
    m = model.get('model')
    return m._meta.app_label if m else ''


@register.filter
def admin_model_icon(model):
    meta = MODEL_META.get((_model_app_label(model), model.get('object_name', '')))
    return meta[0] if meta else DEFAULT_ICON


@register.filter
def admin_model_description(model):
    meta = MODEL_META.get((_model_app_label(model), model.get('object_name', '')))
    return meta[1] if meta else ''
