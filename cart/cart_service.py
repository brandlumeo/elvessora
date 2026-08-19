from decimal import Decimal
from django.conf import settings
from .models import Cart, CartItem


class CartService:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        if not self.session.session_key:
            self.session.create()
        self.session_key = self.session.session_key

    def _get_or_create_cart(self):
        if self.request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=self.request.user, session_key='')
            return cart
        cart, _ = Cart.objects.get_or_create(session_key=self.session_key, user=None)
        return cart

    @property
    def cart(self):
        return self._get_or_create_cart()

    def add_product(self, product, variant=None, quantity=1, gift_wrapping=False, gift_message=''):
        cart = self.cart
        existing = CartItem.objects.filter(cart=cart, product=product, variant=variant, gift_set=None).first()
        new_quantity = (existing.quantity if existing else 0) + quantity
        if variant is not None and new_quantity > variant.stock_quantity:
            raise ValueError(f'Only {variant.stock_quantity} left in stock for {product.name} ({variant.size}).')

        if existing:
            existing.quantity = new_quantity
            existing.gift_wrapping = gift_wrapping
            existing.gift_message = gift_message
            existing.save()
            return existing

        return CartItem.objects.create(
            cart=cart,
            product=product,
            variant=variant,
            gift_set=None,
            quantity=quantity,
            gift_wrapping=gift_wrapping,
            gift_message=gift_message,
        )

    def add_gift_set(self, gift_set, quantity=1, gift_wrapping=False, gift_message=''):
        cart = self.cart
        product = gift_set.products.first()
        if product is None:
            raise ValueError(
                f'Gift set "{gift_set.name}" has no linked products. '
                'Add at least one product in Admin → Gift sets before adding to cart.'
            )
        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            gift_set=gift_set,
            variant=None,
            defaults={
                'quantity': quantity,
                'gift_wrapping': gift_wrapping,
                'gift_message': gift_message,
            },
        )
        if not created:
            item.quantity += quantity
            item.save()
        return item

    def update_quantity(self, item_id, quantity):
        try:
            item = CartItem.objects.get(id=item_id, cart=self.cart)
        except CartItem.DoesNotExist:
            return False
        if quantity <= 0:
            item.delete()
            return True
        if item.variant is not None and quantity > item.variant.stock_quantity:
            raise ValueError(f'Only {item.variant.stock_quantity} left in stock.')
        item.quantity = quantity
        item.save()
        return True

    def remove_item(self, item_id):
        CartItem.objects.filter(id=item_id, cart=self.cart).delete()

    def clear(self):
        self.cart.items.all().delete()

    def apply_coupon(self, code):
        from orders.models import Coupon
        try:
            coupon = Coupon.objects.get(code__iexact=code)
            if coupon.is_valid() and self.cart.subtotal >= coupon.min_order_amount:
                return coupon
        except Coupon.DoesNotExist:
            pass
        return None

    def calculate_totals(self, coupon=None):
        site = __import__('core.models', fromlist=['SiteSettings']).SiteSettings.get()
        subtotal = self.cart.subtotal
        cart_qty = sum(i.quantity for i in self.cart.items.all())
        discount = (
            coupon.calculate_discount(subtotal, cart_quantity=cart_qty)
            if coupon else Decimal('0')
        )
        taxable = subtotal - discount
        tax = taxable * site.tax_rate / 100
        free_ship = (
            (coupon and coupon.grants_free_shipping())
            or subtotal >= site.free_shipping_threshold
        )
        shipping = Decimal('0') if free_ship else site.default_shipping_charge
        total = taxable + tax + shipping
        return {
            'subtotal': subtotal,
            'discount': discount,
            'tax': tax,
            'shipping': shipping,
            'total': total,
        }

    def merge_session_cart(self, user):
        session_cart = Cart.objects.filter(session_key=self.session_key, user=None).first()
        if not session_cart:
            return
        user_cart, _ = Cart.objects.get_or_create(user=user, session_key='')
        for item in session_cart.items.all():
            existing = user_cart.items.filter(
                product=item.product, variant=item.variant, gift_set=item.gift_set
            ).first()
            if existing:
                existing.quantity += item.quantity
                existing.save()
            else:
                item.cart = user_cart
                item.save()
        session_cart.delete()
