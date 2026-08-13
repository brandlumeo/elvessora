from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.urls import path
from django.utils import timezone

from accounts.models import Customer
from core.models import SiteSettings
from orders.models import Order, OrderItem, Payment, Refund
from products.models import Product, ProductVariant


@staff_member_required
def admin_reports_view(request):
    settings = SiteSettings.get()
    threshold = settings.low_stock_threshold
    now = timezone.now()
    paid = Order.objects.filter(payment_status='paid')

    sales_by_day = (
        paid.filter(created_at__gte=now - timezone.timedelta(days=30))
        .annotate(day=TruncDate('created_at'))
        .values('day')
        .annotate(revenue=Sum('total'), orders=Count('id'))
        .order_by('-day')[:30]
    )

    product_perf = (
        OrderItem.objects.filter(order__payment_status='paid')
        .values('product_name')
        .annotate(
            units=Sum('quantity'),
            revenue=Sum(
                ExpressionWrapper(
                    F('unit_price') * F('quantity'),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            ),
        )
        .order_by('-units')[:20]
    )

    customer_stats = {
        'total': Customer.objects.filter(is_staff=False).count(),
        'with_orders': Customer.objects.filter(is_staff=False, orders__isnull=False).distinct().count(),
    }

    inventory_report = {
        'skus': ProductVariant.objects.count(),
        'low_stock': ProductVariant.objects.filter(stock_quantity__lte=threshold)
        .exclude(stock_quantity=0).count(),
        'out_of_stock': ProductVariant.objects.filter(stock_quantity=0).count(),
        'active_products': Product.objects.filter(is_active=True).count(),
    }

    payment_report = {
        'paid_orders': paid.count(),
        'paid_revenue': paid.aggregate(t=Sum('total'))['t'] or 0,
        'pending_payments': Order.objects.filter(payment_status='pending').count(),
        'refunds': Refund.objects.count(),
        'refund_amount': Refund.objects.aggregate(t=Sum('amount'))['t'] or 0,
        'transactions': Payment.objects.count(),
    }

    shipping_report = {
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'with_tracking': Order.objects.exclude(tracking_number='').count(),
        'shipping_collected': Order.objects.aggregate(t=Sum('shipping_charge'))['t'] or 0,
    }

    tax_report = {
        'tax_collected': Order.objects.filter(payment_status='paid').aggregate(t=Sum('tax_amount'))['t'] or 0,
        'store_tax_rate': settings.tax_rate,
    }

    context = {
        **admin.site.each_context(request),
        'title': 'Reports & Analytics',
        'sales_by_day': list(sales_by_day),
        'product_perf': list(product_perf),
        'customer_stats': customer_stats,
        'inventory_report': inventory_report,
        'payment_report': payment_report,
        'shipping_report': shipping_report,
        'tax_report': tax_report,
        'total_revenue': payment_report['paid_revenue'],
        'total_orders': Order.objects.count(),
    }
    return render(request, 'admin/reports.html', context)


_original_get_urls = admin.site.get_urls


def _get_urls():
    return [
        path('reports/', admin.site.admin_view(admin_reports_view), name='elvassora_reports'),
    ] + _original_get_urls()


admin.site.get_urls = _get_urls
