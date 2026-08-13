from django.contrib import admin
from django.db.models import Sum
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


def _period_sales(paid_qs, since):
    return paid_qs.filter(created_at__gte=since).aggregate(total=Sum('total'))['total'] or 0


def admin_dashboard_context():
    settings = SiteSettings.get()
    threshold = settings.low_stock_threshold
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    paid_orders = Order.objects.filter(payment_status='paid')
    total_revenue = paid_orders.aggregate(total=Sum('total'))['total'] or 0

    top_selling = (
        OrderItem.objects.filter(order__payment_status='paid')
        .values('product_name')
        .annotate(qty=Sum('quantity'))
        .order_by('-qty')[:10]
    )

    return {
        'total_sales': total_revenue,
        'total_revenue': total_revenue,
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(
            status__in=['pending', 'confirmed', 'processing']
        ).count(),
        'completed_orders': Order.objects.filter(status='delivered').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        'total_products': Product.objects.filter(is_active=True).count(),
        'total_customers': Customer.objects.filter(is_staff=False).count(),
        'recent_orders': Order.objects.select_related('user').order_by('-created_at')[:8],
        'low_stock_items': ProductVariant.objects.filter(
            stock_quantity__lte=threshold
        ).select_related('product')[:10],
        'low_stock_count': ProductVariant.objects.filter(
            stock_quantity__lte=threshold
        ).count(),
        'top_selling_products': list(top_selling),
        'sales_today': _period_sales(paid_orders, today_start),
        'sales_week': _period_sales(paid_orders, now - timezone.timedelta(days=7)),
        'sales_month': _period_sales(paid_orders, now - timezone.timedelta(days=30)),
        'sales_year': _period_sales(paid_orders, now - timezone.timedelta(days=365)),
        'compulsory_sections': _compulsory_sections(),
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
    extra_context.update(admin_dashboard_context())
    return _original_index(request, extra_context)


admin.site.index = custom_admin_index

admin.site.site_header = 'Elvessora Admin Dashboard'
admin.site.site_title = 'Elvessora Admin'
admin.site.index_title = 'Store Management'
