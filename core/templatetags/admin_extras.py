from django import template
from django.urls import reverse

from core.models import AdminAlertSeen, SiteSettings
from orders.models import Order
from products.models import ProductVariant

register = template.Library()


ALERT_ORDER_STATUSES = ['pending', 'confirmed', 'processing']


def _unseen_alerts(context):
    """Pending orders + low-stock variants this admin hasn't seen yet in the
    bell. Computed once per request and shared by the badge and dropdown.

    Low-stock "seen" marks are dropped once a variant is restocked above the
    threshold, so it alerts again if it later runs low again.
    """
    request = context.get('request')
    cache = getattr(request, '_elv_admin_alerts', None)
    if cache is not None:
        return cache

    user = getattr(request, 'user', None)
    seen = set()
    if user is not None and user.is_authenticated:
        seen = set(AdminAlertSeen.objects.filter(user=user).values_list('key', flat=True))

    threshold = SiteSettings.get().low_stock_threshold
    orders = [
        o for o in Order.objects.filter(status__in=ALERT_ORDER_STATUSES).order_by('-created_at')
        .only('pk', 'order_number', 'status', 'shipping_name')
        if f'order:{o.pk}' not in seen
    ]
    low_variants = list(
        ProductVariant.objects.filter(stock_quantity__lte=threshold)
        .select_related('product').order_by('stock_quantity')
    )
    low_keys = {f'stock:{v.pk}' for v in low_variants}
    restocked = {k for k in seen if k.startswith('stock:') and k not in low_keys}
    if restocked:
        AdminAlertSeen.objects.filter(user=user, key__in=restocked).delete()
    variants = [v for v in low_variants if f'stock:{v.pk}' not in seen]

    alerts = {'orders': orders, 'variants': variants}
    if request is not None:
        request._elv_admin_alerts = alerts
    return alerts


@register.simple_tag(takes_context=True)
def admin_alert_count(context):
    """Unseen pending orders + low-stock variants — the bell's badge."""
    alerts = _unseen_alerts(context)
    return len(alerts['orders']) + len(alerts['variants'])


@register.simple_tag(takes_context=True)
def admin_alert_items(context, limit=6):
    """Unseen pending orders + low-stock variants for the bell dropdown.
    Each item carries a ``key`` the page posts back once the bell is opened."""
    alerts = _unseen_alerts(context)
    items = []

    for order in alerts['orders'][:limit]:
        items.append({
            'key': f'order:{order.pk}',
            'icon': 'bi-bag-check',
            'title': f'Order #{order.order_number}',
            'subtitle': f'{order.get_status_display()} — {order.shipping_name}',
            'url': reverse('admin:orders_order_change', args=[order.pk]),
        })

    for variant in alerts['variants'][:limit]:
        items.append({
            'key': f'stock:{variant.pk}',
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
