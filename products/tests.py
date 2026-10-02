from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from .admin import ProductAdmin
from .models import Product, ProductVariant


class PriceSyncTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name='Divine Aura', sku='DA', description='x', regular_price=Decimal('85'),
        )
        self.small = ProductVariant.objects.create(
            product=self.product, size='50ml', sku='DA-50', price=Decimal('85'), stock_quantity=5,
        )
        self.large = ProductVariant.objects.create(
            product=self.product, size='100ml', sku='DA-100', price=Decimal('119'), stock_quantity=5,
        )
        self.admin = ProductAdmin(Product, AdminSite())

    def save_with(self, changed, **prices):
        for field, value in prices.items():
            setattr(self.product, field, value)
        self.product.save()
        form = SimpleNamespace(instance=self.product, changed_data=changed)
        request = RequestFactory().post('/')
        with mock.patch('django.contrib.admin.ModelAdmin.save_related'), \
                mock.patch('django.contrib.messages.info'):
            self.admin.save_related(request, form, [], True)
        self.small.refresh_from_db()
        self.large.refresh_from_db()

    def test_sizes_sort_by_ml_not_text(self):
        self.assertEqual(self.product.default_variant, self.small)
        self.assertEqual(self.product.base_variant, self.small)

    def test_default_variant_skips_out_of_stock(self):
        self.small.stock_quantity = 0
        self.small.save()
        self.assertEqual(self.product.default_variant, self.large)

    def test_price_edit_updates_base_size_only(self):
        self.save_with(['regular_price'], regular_price=Decimal('1.00'))
        self.assertEqual(self.small.price, Decimal('1.00'))
        self.assertEqual(self.large.price, Decimal('119.00'))

    def test_offer_price_is_synced_too(self):
        self.save_with(['offer_price'], offer_price=Decimal('70.00'))
        self.assertEqual(self.small.offer_price, Decimal('70.00'))
        self.assertEqual(self.small.current_price, Decimal('70.00'))

    def test_unrelated_edit_leaves_sizes_alone(self):
        self.small.price = Decimal('90')
        self.small.save()
        self.save_with(['name'])
        self.assertEqual(self.small.price, Decimal('90.00'))
