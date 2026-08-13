from django.contrib import admin
from django.urls import path, reverse
from django.utils.html import format_html
from .models import Coupon, Order, OrderItem, Payment, Refund
from . import admin_print


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'variant_size', 'quantity', 'unit_price']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 'buy_quantity', 'get_quantity',
        'valid_until', 'used_count', 'max_uses', 'is_active',
    ]
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code']
    list_editable = ['is_active']
    date_hierarchy = 'valid_until'
    readonly_fields = ['used_count']
    fieldsets = (
        (None, {'fields': ('code', 'description', 'discount_type', 'discount_value', 'is_active')}),
        ('Buy X Get Y', {
            'fields': ('buy_quantity', 'get_quantity'),
            'description': 'Only used when discount type is Buy X Get Y.',
        }),
        ('Limits', {'fields': ('min_order_amount', 'max_uses', 'used_count', 'valid_from', 'valid_until')}),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'shipping_name', 'total', 'status', 'payment_status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'shipping_name', 'shipping_phone', 'guest_email']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'print_documents']
    inlines = [OrderItemInline]
    list_editable = ['status', 'payment_status']

    fieldsets = (
        ('Order Info', {'fields': ('order_number', 'user', 'is_guest', 'guest_email', 'status', 'created_at', 'print_documents')}),
        ('Shipping', {'fields': ('shipping_name', 'shipping_phone', 'shipping_address', 'shipping_city', 'shipping_state', 'shipping_pincode', 'shipping_country')}),
        ('Pricing', {'fields': ('subtotal', 'shipping_charge', 'tax_amount', 'discount_amount', 'total', 'coupon', 'coupon_code')}),
        ('Payment', {'fields': ('payment_method', 'payment_status', 'razorpay_order_id', 'razorpay_payment_id')}),
        ('Delivery', {'fields': ('tracking_number', 'courier_name', 'estimated_delivery', 'notes')}),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                '<path:object_id>/invoice/',
                self.admin_site.admin_view(admin_print.order_invoice),
                name='orders_order_invoice',
            ),
            path(
                '<path:object_id>/packing-slip/',
                self.admin_site.admin_view(admin_print.order_packing_slip),
                name='orders_order_packing_slip',
            ),
        ]
        return custom + urls

    @admin.display(description='Documents')
    def print_documents(self, obj):
        if not obj.pk:
            return '—'
        invoice = reverse('admin:orders_order_invoice', args=[obj.pk])
        packing = reverse('admin:orders_order_packing_slip', args=[obj.pk])
        return format_html(
            '<a class="button" href="{}" target="_blank" rel="noopener">Invoice</a>&nbsp;'
            '<a class="button" href="{}" target="_blank" rel="noopener">Packing Slip</a>',
            invoice,
            packing,
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'status', 'created_at']
    list_filter = ['status']


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'status', 'created_at']
    list_filter = ['status']
    list_editable = ['status']
