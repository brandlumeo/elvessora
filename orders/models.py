from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid


class Coupon(models.Model):
    DISCOUNT_TYPES = [
        ('percent', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free_shipping', 'Free Shipping'),
        ('bxgy', 'Buy X Get Y'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percent')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    buy_quantity = models.PositiveIntegerField(
        default=1, help_text='Buy X (for Buy X Get Y coupons)'
    )
    get_quantity = models.PositiveIntegerField(
        default=1, help_text='Get Y free (for Buy X Get Y coupons)'
    )
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-valid_from']

    def is_valid(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses and self.used_count >= self.max_uses:
            return False
        return True

    def calculate_discount(self, subtotal, cart_quantity=0):
        from decimal import Decimal
        if not self.is_valid() or subtotal < self.min_order_amount:
            return Decimal('0')
        if self.discount_type == 'free_shipping':
            return Decimal('0')
        if self.discount_type == 'bxgy':
            # Approximate: value of free units as average unit price * get_qty sets
            if cart_quantity < self.buy_quantity + self.get_quantity:
                return Decimal('0')
            sets = cart_quantity // (self.buy_quantity + self.get_quantity)
            if sets <= 0 or cart_quantity <= 0:
                return Decimal('0')
            avg = subtotal / cart_quantity
            return (avg * self.get_quantity * sets).quantize(Decimal('0.01'))
        if self.discount_type == 'percent':
            return subtotal * self.discount_value / 100
        return min(self.discount_value, subtotal)

    def grants_free_shipping(self):
        return self.is_valid() and self.discount_type == 'free_shipping'

    def __str__(self):
        return self.code


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    PAYMENT_METHODS = [
        ('razorpay', 'Online Payment'),
        ('tamara', 'Pay in Installments (Tamara)'),
        ('tabby', 'Pay in 4 (Tabby)'),
        ('cod', 'Cash on Delivery'),
    ]
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    is_guest = models.BooleanField(default=False)
    guest_email = models.EmailField(blank=True)

    shipping_name = models.CharField(max_length=150)
    shipping_phone = models.CharField(max_length=20)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_pincode = models.CharField(max_length=10)
    shipping_country = models.CharField(max_length=100, default='United Arab Emirates')

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    coupon_code = models.CharField(max_length=50, blank=True)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    tamara_order_id = models.CharField(max_length=100, blank=True)
    tamara_checkout_id = models.CharField(max_length=100, blank=True)
    tabby_payment_id = models.CharField(max_length=100, blank=True)
    amazon_fulfillment_status = models.CharField(max_length=50, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    tracking_number = models.CharField(max_length=100, blank=True)
    courier_name = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f'ELV{uuid.uuid4().hex[:8].upper()}'
            
        trigger_mcf = False
        if self.pk:
            try:
                old = Order.objects.get(pk=self.pk)
                if old.status != 'confirmed' and self.status == 'confirmed':
                    trigger_mcf = True
            except Order.DoesNotExist:
                if self.status == 'confirmed':
                    trigger_mcf = True
        else:
            if self.status == 'confirmed':
                trigger_mcf = True
                
        super().save(*args, **kwargs)
        
        if trigger_mcf:
            try:
                from . import amazon_mcf
                amazon_mcf.create_fulfillment_order(self)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error('Failed to trigger MCF: %s', e)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.SET_NULL, null=True, blank=True)
    gift_set = models.ForeignKey('products.GiftSet', on_delete=models.SET_NULL, null=True, blank=True)
    product_name = models.CharField(max_length=200)
    variant_size = models.CharField(max_length=20, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    gift_message = models.TextField(blank=True)
    gift_wrapping = models.BooleanField(default=False)

    @property
    def line_total(self):
        total = self.unit_price * self.quantity
        if self.gift_wrapping:
            from decimal import Decimal
            total += Decimal('49.00')
        return total

    def __str__(self):
        return f'{self.product_name} x {self.quantity}'


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Payment for {self.order.order_number}'


class Refund(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('rejected', 'Rejected'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Refund {self.order.order_number} - {self.status}'
