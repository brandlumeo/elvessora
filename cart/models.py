from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='carts')
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    @property
    def subtotal(self):
        return sum(item.line_total for item in self.items.all())

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

    def __str__(self):
        return f'Cart {self.id}'


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    variant = models.ForeignKey('products.ProductVariant', on_delete=models.CASCADE, null=True, blank=True)
    gift_set = models.ForeignKey('products.GiftSet', on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    gift_message = models.TextField(blank=True)
    gift_wrapping = models.BooleanField(default=False)

    class Meta:
        ordering = ['id']

    @property
    def unit_price(self):
        if self.gift_set:
            return self.gift_set.current_price
        if self.variant:
            return self.variant.current_price
        return self.product.current_price

    @property
    def line_total(self):
        total = self.unit_price * self.quantity
        if self.gift_wrapping:
            total += Decimal('49.00')
        return total

    def __str__(self):
        name = self.gift_set.name if self.gift_set else self.product.name
        return f'{name} x {self.quantity}'
