from django import template

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
