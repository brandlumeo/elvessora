from products.models import ProductVariant
from django.conf import settings
from django.db import models


class Inventory(ProductVariant):
    """Proxy — stock management per product variant (50ml, 100ml, etc.)."""

    class Meta:
        proxy = True
        verbose_name = 'Stock Item'
        verbose_name_plural = 'Inventory'


class Warehouse(models.Model):
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='United Arab Emirates')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.is_default:
            Warehouse.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.code})'


class StockAdjustment(models.Model):
    ADJUST_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('set', 'Set Absolute'),
        ('correction', 'Correction'),
    ]

    variant = models.ForeignKey(
        'products.ProductVariant', on_delete=models.CASCADE, related_name='stock_adjustments'
    )
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.SET_NULL, null=True, blank=True, related_name='adjustments'
    )
    adjustment_type = models.CharField(max_length=20, choices=ADJUST_TYPES, default='correction')
    quantity_change = models.IntegerField(
        help_text='Delta for In/Out/Correction; absolute target quantity for Set Absolute.'
    )
    quantity_before = models.PositiveIntegerField(default=0)
    quantity_after = models.PositiveIntegerField(default=0)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Inventory history'
        verbose_name_plural = 'Inventory history'

    def save(self, *args, apply_stock=True, **kwargs):
        is_new = self.pk is None
        if is_new and apply_stock:
            variant = self.variant
            self.quantity_before = variant.stock_quantity
            if self.adjustment_type == 'set':
                new_qty = max(0, self.quantity_change)
            elif self.adjustment_type == 'in':
                new_qty = variant.stock_quantity + abs(self.quantity_change)
            elif self.adjustment_type == 'out':
                new_qty = max(0, variant.stock_quantity - abs(self.quantity_change))
            else:
                new_qty = max(0, variant.stock_quantity + self.quantity_change)
            self.quantity_after = new_qty
            super().save(*args, **kwargs)
            if variant.stock_quantity != new_qty:
                variant.stock_quantity = new_qty
                variant.save(update_fields=['stock_quantity'])
            return
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.variant} {self.quantity_before}→{self.quantity_after}'
