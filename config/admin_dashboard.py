from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate, TruncMonth
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from accounts.models import Customer
from cart.models import Cart
from core.models import SiteSettings, FAQ
from marketing.models import AbandonedCartReminder
from orders.models import Order, OrderItem
from products.models import Product, ProductVariant, RecentlyViewed


def _admin_url(name, *args):
    try:
        return reverse(name, args=args) if args else reverse(name)
    except NoReverseMatch:
        return '#'


def _hide_non_compulsory_admin_models():
    """Hide only noisy / non-daily models. Phase-1 models stay visible."""
    optional = (
        RecentlyViewed,
        Cart,
        AbandonedCartReminder,
        FAQ,
        ProductVariant,
    )
    for model in optional:
        try:
            admin.site.unregister(model)
        except admin.sites.NotRegistered:
            pass


_hide_non_compulsory_admin_models()


GCC_FLAGS = {
    'united arab emirates': ('UAE', '\U0001F1E6\U0001F1EA'),
    'uae': ('UAE', '\U0001F1E6\U0001F1EA'),
    'saudi arabia': ('Saudi Arabia', '\U0001F1F8\U0001F1E6'),
    'kuwait': ('Kuwait', '\U0001F1F0\U0001F1FC'),
    'qatar': ('Qatar', '\U0001F1F6\U0001F1E6'),
    'oman': ('Oman', '\U0001F1F4\U0001F1F2'),
    'bahrain': ('Bahrain', '\U0001F1E7\U0001F1ED'),
}

PAYMENT_LABELS = {
    'razorpay': 'Card',
    'tamara': 'Tamara',
    'cod': 'Cash on Delivery',
}

STATUS_COLORS = {
    'pending': 'grey',
    'confirmed': 'blue',
    'processing': 'amber',
    'shipped': 'blue',
    'out_for_delivery': 'amber',
    'delivered': 'green',
    'cancelled': 'red',
    'refunded': 'red',
}

RANGE_CHOICES = {
    '7d': ('This Week', 7),
    '30d': ('This Month', 30),
    '90d': ('Last 90 Days', 90),
    '365d': ('This Year', 365),
}


def _country_display(name):
    key = (name or '').strip().lower()
    if key in GCC_FLAGS:
        return GCC_FLAGS[key]
    return ((name or 'Unknown').strip() or 'Unknown', '\U0001F30D')


def _pct_change(current, previous):
    current = float(current or 0)
    previous = float(previous or 0)
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


def _trend(change):
    """Pre-render the up/down class + label so templates never compare None."""
    if change is None:
        return {'dir': '', 'text': 'No prior-period data'}
    if change > 0:
        return {'dir': 'up', 'text': f'↑ {change}% vs prior period'}
    if change < 0:
        return {'dir': 'down', 'text': f'↓ {abs(change)}% vs prior period'}
    return {'dir': '', 'text': 'No change vs prior period'}


def _buyer_counts(before=None):
    """(total distinct buyers, buyers with more than one paid order)."""
    orders_qs = Order.objects.filter(payment_status='paid', user__isnull=False)
    if before is not None:
        orders_qs = orders_qs.filter(created_at__lt=before)
    counts = orders_qs.values('user').annotate(n=Count('id'))
    total_buyers = counts.count()
    repeat_buyers = counts.filter(n__gt=1).count()
    return total_buyers, repeat_buyers


def admin_dashboard_context(request):
    settings_obj = SiteSettings.get()
    threshold = settings_obj.low_stock_threshold
    now = timezone.now()

    range_key = request.GET.get('range', '7d')
    if range_key not in RANGE_CHOICES:
        range_key = '7d'
    range_label, range_days = RANGE_CHOICES[range_key]
    period_start = now - timedelta(days=range_days)
    prev_period_start = period_start - timedelta(days=range_days)

    country_filter = (request.GET.get('country') or '').strip()

    paid_orders = Order.objects.filter(payment_status='paid')
    all_countries = list(
        Order.objects.exclude(shipping_country='')
        .values_list('shipping_country', flat=True)
        .distinct()
        .order_by('shipping_country')
    )

    period_orders = paid_orders.filter(created_at__gte=period_start)
    prev_period_orders = paid_orders.filter(created_at__gte=prev_period_start, created_at__lt=period_start)
    if country_filter:
        period_orders = period_orders.filter(shipping_country=country_filter)
        prev_period_orders = prev_period_orders.filter(shipping_country=country_filter)

    period_revenue = period_orders.aggregate(t=Sum('total'))['t'] or 0
    prev_revenue = prev_period_orders.aggregate(t=Sum('total'))['t'] or 0
    period_order_count = period_orders.count()
    prev_order_count = prev_period_orders.count()
    avg_order_value = (period_revenue / period_order_count) if period_order_count else 0
    prev_avg_order_value = (prev_revenue / prev_order_count) if prev_order_count else 0

    total_customers_now = Customer.objects.filter(is_staff=False).count()
    total_customers_prev = Customer.objects.filter(is_staff=False, date_joined__lt=period_start).count()

    total_buyers_now, repeat_buyers_now = _buyer_counts()
    total_buyers_prev, repeat_buyers_prev = _buyer_counts(before=period_start)
    repeat_rate_now = (repeat_buyers_now / total_buyers_now * 100) if total_buyers_now else 0
    repeat_rate_prev = (repeat_buyers_prev / total_buyers_prev * 100) if total_buyers_prev else 0

    returning_customers = repeat_buyers_now
    new_customers = max(total_customers_now - returning_customers, 0)
    returning_customers_prev = repeat_buyers_prev
    new_customers_prev = max(total_customers_prev - returning_customers_prev, 0)
    customer_pie_total = total_customers_now or 1

    # Sales overview chart — daily buckets under 90 days, monthly beyond.
    trunc_fn = TruncMonth if range_days > 90 else TruncDate
    chart_rows = (
        period_orders.annotate(bucket=trunc_fn('created_at'))
        .values('bucket')
        .annotate(revenue=Sum('total'))
        .order_by('bucket')
    )
    chart_labels, chart_values = [], []
    for row in chart_rows:
        bucket = row['bucket']
        chart_labels.append(bucket.strftime('%b %Y') if range_days > 90 else bucket.strftime('%b %d'))
        chart_values.append(float(row['revenue'] or 0))

    # GCC country breakdown — always the full spread for the selected range,
    # independent of the country filter (which scopes the headline stats/chart).
    gcc_rows = (
        paid_orders.filter(created_at__gte=period_start)
        .values('shipping_country')
        .annotate(total=Sum('total'))
        .order_by('-total')
    )
    gcc_total = sum(float(row['total'] or 0) for row in gcc_rows) or 1
    palette = ['#163A8A', '#C8A96A', '#526694', '#2E7D4F', '#B8860B', '#8A5FA8']
    gcc_breakdown = []
    for i, row in enumerate(gcc_rows):
        label, flag = _country_display(row['shipping_country'])
        amount = float(row['total'] or 0)
        gcc_breakdown.append({
            'label': label,
            'flag': flag,
            'total': amount,
            'pct': round(amount / gcc_total * 100, 1),
            'color': palette[i % len(palette)],
        })

    # Top selling perfumes within the selected range/country.
    top_items = (
        OrderItem.objects.filter(order__in=period_orders)
        .exclude(product__isnull=True)
        .values('product__id', 'product__name', 'product__slug')
        .annotate(
            qty=Sum('quantity'),
            revenue=Sum(
                ExpressionWrapper(
                    F('unit_price') * F('quantity'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
        )
        .order_by('-qty')[:5]
    )
    top_selling = []
    for row in top_items:
        image_url = ''
        product = Product.objects.filter(pk=row['product__id']).prefetch_related('images').first()
        if product:
            image = product.images.filter(is_primary=True).first() or product.images.first()
            if image and image.image:
                image_url = image.image.url
        top_selling.append({
            'name': row['product__name'],
            'slug': row['product__slug'],
            'qty': row['qty'],
            'revenue': row['revenue'] or 0,
            'image_url': image_url,
        })

    recent_orders = []
    for order in Order.objects.select_related('user').order_by('-created_at')[:8]:
        label, flag = _country_display(order.shipping_country)
        recent_orders.append({
            'order': order,
            'country_label': label,
            'country_flag': flag,
            'payment_label': PAYMENT_LABELS.get(order.payment_method, order.get_payment_method_display()),
            'status_color': STATUS_COLORS.get(order.status, 'grey'),
        })

    low_stock_items = ProductVariant.objects.filter(stock_quantity__lte=threshold).select_related('product')[:10]

    new_pct = round(new_customers / customer_pie_total * 100, 1)
    returning_pct = round(returning_customers / customer_pie_total * 100, 1)

    chart_data = {
        'labels': chart_labels,
        'values': chart_values,
        'gcc_labels': [row['label'] for row in gcc_breakdown],
        'gcc_values': [row['total'] for row in gcc_breakdown],
        'gcc_colors': [row['color'] for row in gcc_breakdown],
        'customer_labels': ['New', 'Returning'],
        'customer_values': [new_pct, returning_pct],
        'customer_colors': ['#C8A96A', '#163A8A'],
    }

    return {
        'range_key': range_key,
        'range_label': range_label,
        'range_choices': RANGE_CHOICES,
        'country_filter': country_filter,
        'all_countries': all_countries,

        'period_revenue': period_revenue,
        'revenue_trend': _trend(_pct_change(period_revenue, prev_revenue)),
        'period_order_count': period_order_count,
        'orders_trend': _trend(_pct_change(period_order_count, prev_order_count)),
        'total_customers': total_customers_now,
        'customers_trend': _trend(_pct_change(total_customers_now, total_customers_prev)),
        'repeat_rate': round(repeat_rate_now, 1),
        'repeat_trend': _trend(_pct_change(repeat_rate_now, repeat_rate_prev)),
        'avg_order_value': avg_order_value,
        'aov_trend': _trend(_pct_change(avg_order_value, prev_avg_order_value)),

        'chart_labels': chart_labels,
        'chart_values': chart_values,
        'gcc_breakdown': gcc_breakdown,

        'top_selling': top_selling,
        'recent_orders': recent_orders,

        'new_customers': new_customers,
        'new_customers_trend': _trend(_pct_change(new_customers, new_customers_prev)),
        'returning_customers': returning_customers,
        'returning_customers_trend': _trend(_pct_change(returning_customers, returning_customers_prev)),
        'new_customers_pct': new_pct,
        'returning_customers_pct': returning_pct,

        'total_products': Product.objects.filter(is_active=True).count(),
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_items.count(),
        'compulsory_sections': _compulsory_sections(),
        'chart_data': chart_data,
    }


def _compulsory_sections():
    return [
        {
            'num': 1,
            'title': 'Dashboard',
            'priority': 'High',
            'icon': 'bi-grid-1x2',
            'url': _admin_url('admin:index'),
            'items': [
                'Total Revenue', 'Total Orders', 'Customers',
                'Pending / Completed / Cancelled', 'Sales Analytics', 'Top Sellers',
            ],
        },
        {
            'num': 2,
            'title': 'Store Settings',
            'priority': 'High',
            'icon': 'bi-gear',
            'url': _admin_url('admin:core_sitesettings_change', 1),
            'items': [
                'Brand name, logo, tagline', 'Phone, WhatsApp, Email',
                'Business address', 'Shipping charge & free shipping limit',
                'Tax/GST rate', 'Social media links',
            ],
        },
        {
            'num': 3,
            'title': 'Products',
            'priority': 'High',
            'icon': 'bi-droplet',
            'url': _admin_url('admin:products_product_changelist'),
            'items': [
                'Name, SKU, barcode, brand', 'Price & offer price',
                'Notes, longevity, sillage', 'Variants & images',
                'Active / Featured flags',
            ],
        },
        {
            'num': 4,
            'title': 'Categories',
            'priority': 'Medium',
            'icon': 'bi-folder',
            'url': _admin_url('admin:products_category_changelist'),
            'items': ['Parent & child categories', 'Image & banner'],
        },
        {
            'num': 5,
            'title': 'Collections',
            'priority': 'Medium',
            'icon': 'bi-collection',
            'url': _admin_url('admin:products_collection_changelist'),
            'items': ['Seasonal, luxury, gift, featured'],
        },
        {
            'num': 6,
            'title': 'Inventory',
            'priority': 'High',
            'icon': 'bi-boxes',
            'url': _admin_url('admin:inventory_inventory_changelist'),
            'items': [
                'Stock quantity per variant', 'Low stock alerts', 'Update stock',
            ],
        },
        {
            'num': 7,
            'title': 'Orders',
            'priority': 'High',
            'icon': 'bi-bag-check',
            'url': _admin_url('admin:orders_order_changelist'),
            'items': [
                'Order list & details', 'Status & tracking',
                'Invoice & packing slip', 'Payments & refunds',
            ],
        },
        {
            'num': 8,
            'title': 'Customers',
            'priority': 'Medium',
            'icon': 'bi-people',
            'url': _admin_url('admin:accounts_customer_changelist'),
            'items': ['Customer list', 'Profiles, addresses, wishlist'],
        },
        {
            'num': 9,
            'title': 'Reviews',
            'priority': 'Medium',
            'icon': 'bi-star',
            'url': _admin_url('admin:reviews_review_changelist'),
            'items': ['Approve / reject', 'Featured reviews'],
        },
        {
            'num': 10,
            'title': 'Coupons',
            'priority': 'Medium',
            'icon': 'bi-tag',
            'url': _admin_url('admin:orders_coupon_changelist'),
            'items': ['Discount codes', 'Percentage or flat discount', 'Expiry date'],
        },
        {
            'num': 11,
            'title': 'Banners & Homepage',
            'priority': 'Medium',
            'icon': 'bi-image',
            'url': _admin_url('admin:marketing_banner_changelist'),
            'items': ['Hero & promo banners', 'Homepage sections', 'Promo popup'],
        },
        {
            'num': 12,
            'title': 'Newsletter',
            'priority': 'Medium',
            'icon': 'bi-envelope',
            'url': _admin_url('admin:marketing_newslettersubscriber_changelist'),
            'items': ['Subscriber list', 'Export CSV'],
        },
        {
            'num': 13,
            'title': 'Enquiries',
            'priority': 'Medium',
            'icon': 'bi-chat-dots',
            'url': _admin_url('admin:marketing_contactenquiry_changelist'),
            'items': ['Contact & wholesale messages'],
        },
        {
            'num': 14,
            'title': 'Gift Sets',
            'priority': 'Medium',
            'icon': 'bi-gift',
            'url': _admin_url('admin:products_giftset_changelist'),
            'items': ['Gift boxes & mini collections'],
        },
        {
            'num': 15,
            'title': 'Users & Roles',
            'priority': 'High',
            'icon': 'bi-shield-lock',
            'url': _admin_url('admin:auth_user_changelist'),
            'items': ['Admin & staff users', 'Groups & permissions', 'Login history'],
        },
        {
            'num': 16,
            'title': 'Reports',
            'priority': 'High',
            'icon': 'bi-graph-up',
            'url': _admin_url('admin:elvassora_reports'),
            'items': [
                'Sales & revenue', 'Product performance',
                'Inventory, payment, shipping, tax',
            ],
        },
        {
            'num': 17,
            'title': 'Shipping',
            'priority': 'Medium',
            'icon': 'bi-truck',
            'url': _admin_url('admin:core_shippingzone_changelist'),
            'items': ['Providers', 'Zones', 'Country rates'],
        },
        {
            'num': 18,
            'title': 'Countries & Currency',
            'priority': 'Medium',
            'icon': 'bi-globe',
            'url': _admin_url('admin:core_country_changelist'),
            'items': ['Countries', 'Currencies', 'Region pricing'],
        },
        {
            'num': 19,
            'title': 'Blog',
            'priority': 'Medium',
            'icon': 'bi-journal-text',
            'url': _admin_url('admin:blog_blogpost_changelist'),
            'items': ['Posts', 'Categories', 'SEO fields'],
        },
        {
            'num': 20,
            'title': 'Warehouses',
            'priority': 'Medium',
            'icon': 'bi-building',
            'url': _admin_url('admin:inventory_stockadjustment_changelist'),
            'items': ['Warehouses', 'Stock adjustments / history'],
        },
        {
            'num': 21,
            'title': 'Flash Sales',
            'priority': 'Medium',
            'icon': 'bi-lightning',
            'url': _admin_url('admin:marketing_flashsale_changelist'),
            'items': ['Timed product discounts'],
        },
        {
            'num': 22,
            'title': 'Legal Pages',
            'priority': 'Medium',
            'icon': 'bi-file-text',
            'url': _admin_url('admin:core_legalpage_changelist'),
            'items': [
                'Privacy Policy', 'Terms & Conditions',
                'Shipping Policy', 'Return & Refund Policy',
            ],
        },
    ]


_original_index = admin.site.index


def custom_admin_index(request, extra_context=None):
    extra_context = extra_context or {}
    extra_context.update(admin_dashboard_context(request))
    return _original_index(request, extra_context)


admin.site.index = custom_admin_index

admin.site.site_header = 'Elvessora Admin Dashboard'
admin.site.site_title = 'Elvessora Admin'
admin.site.index_title = 'Store Management'
