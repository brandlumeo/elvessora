import base64
import hashlib
import hmac
import json
import time
from decimal import Decimal
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from products.models import Product, ProductVariant

from . import nomod
from .forms import CheckoutForm
from .models import Order, OrderItem
from .views import ORDER_ACCESS_SESSION_KEY

WEBHOOK_KEY = b'test-signing-key-0123456789'
WEBHOOK_SECRET = 'whsec_' + base64.b64encode(WEBHOOK_KEY).decode()


def sign(body, msg_id='msg_1', timestamp=None, key=WEBHOOK_KEY):
    timestamp = str(int(time.time()) if timestamp is None else timestamp)
    signed = f'{msg_id}.{timestamp}.{body}'.encode()
    sig = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()
    return {
        'HTTP_SVIX_ID': msg_id,
        'HTTP_SVIX_TIMESTAMP': timestamp,
        'HTTP_SVIX_SIGNATURE': f'v1,{sig}',
    }


# Plain static storage so pages render without a collectstatic manifest.
TEST_STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}


@override_settings(NOMOD_API_KEY='sk_test_x', NOMOD_WEBHOOK_SECRET=WEBHOOK_SECRET, STORAGES=TEST_STORAGES)
class NomodTestBase(TestCase):
    def setUp(self):
        product = Product.objects.create(
            name='Divine Aura', sku='DA', description='x', regular_price=Decimal('300'),
        )
        self.variant = ProductVariant.objects.create(
            product=product, size='50ml', sku='DA-50', price=Decimal('300'), stock_quantity=10,
        )
        self.order = Order.objects.create(
            guest_email='a@example.com', shipping_name='Sara Ali', shipping_phone='050 123 4567',
            shipping_address='x', shipping_city='Dubai', shipping_state='Dubai', shipping_pincode='0',
            subtotal=Decimal('600.00'), shipping_charge=Decimal('25.00'), tax_amount=Decimal('27.50'),
            discount_amount=Decimal('50.00'), total=Decimal('602.50'),
            payment_method='nomod', nomod_checkout_id='chk_1',
        )
        OrderItem.objects.create(
            order=self.order, product=product, variant=self.variant, product_name='Divine Aura',
            variant_size='50ml', quantity=2, unit_price=Decimal('300.00'),
        )

    def checkout(self, **overrides):
        data = {
            'id': 'chk_1', 'status': 'paid', 'currency': 'AED',
            'amount': '602.50', 'reference_id': self.order.order_number,
        }
        data.update(overrides)
        return data

    def grant_session(self):
        session = self.client.session
        session[ORDER_ACCESS_SESSION_KEY] = [self.order.order_number]
        session.save()


class NomodPayloadTests(NomodTestBase):
    def test_items_add_up_to_amount(self):
        with mock.patch.object(nomod, '_request', return_value={'id': 'c', 'url': 'https://pay'}) as req:
            nomod.create_checkout(self.order, 'https://s', 'https://f', 'https://c')
        payload = req.call_args.kwargs['json']
        items_total = sum(Decimal(i['total_amount']) for i in payload['items'])
        self.assertEqual(payload['currency'], 'AED')
        self.assertEqual(payload['amount'], '602.50')
        self.assertEqual(items_total - Decimal(payload['discount']), Decimal(payload['amount']))
        self.assertEqual(payload['customer']['phone_number'], '+971501234567')
        self.assertEqual(payload['reference_id'], self.order.order_number)

    def test_single_word_name_sends_no_customer(self):
        # Nomod rejects a customer without both names, and repeating the
        # first name as the last ("Akash Akash") looks wrong.
        self.order.shipping_name = 'Akash'
        with mock.patch.object(nomod, '_request', return_value={'id': 'c', 'url': 'https://pay'}) as req:
            nomod.create_checkout(self.order, 'https://s', 'https://f', 'https://c')
        self.assertNotIn('customer', req.call_args.kwargs['json'])

    def test_phone_normalisation(self):
        self.assertEqual(nomod._e164_phone('+971 50 123 4567'), '+971501234567')
        self.assertEqual(nomod._e164_phone('00971501234567'), '+971501234567')
        self.assertEqual(nomod._e164_phone(''), '')


class NomodVerificationTests(NomodTestBase):
    def test_paid_checkout_for_this_order(self):
        self.assertTrue(nomod.is_paid_for_order(self.checkout(), self.order))

    def test_rejects_wrong_amount_currency_reference_or_status(self):
        self.assertFalse(nomod.is_paid_for_order(self.checkout(amount='1.00'), self.order))
        self.assertFalse(nomod.is_paid_for_order(self.checkout(currency='USD'), self.order))
        self.assertFalse(nomod.is_paid_for_order(self.checkout(reference_id='ELVOTHER'), self.order))
        self.assertFalse(nomod.is_paid_for_order(self.checkout(status='created'), self.order))


class NomodReturnTests(NomodTestBase):
    def test_success_marks_paid_once_and_decrements_stock(self):
        self.grant_session()
        url = reverse('orders:nomod_success') + f'?order={self.order.order_number}'
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout()):
            response = self.client.get(url)
            self.client.get(url)  # a repeat hit must not decrement stock again
        self.assertRedirects(response, reverse('orders:order_confirmation', args=[self.order.order_number]),
                             fetch_redirect_response=False)
        self.order.refresh_from_db()
        self.variant.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(self.variant.stock_quantity, 8)

    def test_success_redirect_alone_does_not_mark_paid(self):
        self.grant_session()
        url = reverse('orders:nomod_success') + f'?order={self.order.order_number}'
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout(amount='1.00')), \
                mock.patch('orders.views.time.sleep'):
            self.client.get(url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'pending')

    def test_failure_marks_failed_and_page_renders(self):
        self.grant_session()
        url = reverse('orders:nomod_failure') + f'?order={self.order.order_number}'
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout(status='created')):
            response = self.client.get(url, follow=True)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'failed')
        self.assertContains(response, 'Payment not completed')

    def test_cancel_keeps_order_as_cancelled(self):
        self.grant_session()
        url = reverse('orders:nomod_cancel') + f'?order={self.order.order_number}'
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout(status='cancelled')):
            response = self.client.get(url)
        self.assertRedirects(response, reverse('cart:cart'), fetch_redirect_response=False)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')
        self.assertEqual(self.order.payment_status, 'failed')

    def test_expired_checkout_is_cancelled(self):
        self.grant_session()
        url = reverse('orders:nomod_success') + f'?order={self.order.order_number}'
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout(status='expired')):
            self.client.get(url)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'cancelled')

    def test_other_session_is_not_shown_the_order(self):
        url = reverse('orders:nomod_success') + f'?order={self.order.order_number}'
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout()):
            response = self.client.get(url)
        self.assertRedirects(response, reverse('orders:tracking'), fetch_redirect_response=False)


class NomodWebhookTests(NomodTestBase):
    url = reverse('orders:nomod_webhook')

    def post(self, payload, **headers):
        body = json.dumps(payload)
        return self.client.post(self.url, body, content_type='application/json', **(headers or sign(body)))

    def test_valid_webhook_refetches_and_marks_paid(self):
        payload = {'type': 'charge.completed', 'eventId': 'e1', 'data': {'checkout_id': 'chk_1', 'status': 'paid'}}
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout()) as get:
            response = self.post(payload)
        self.assertEqual(response.status_code, 200)
        get.assert_called_once_with('chk_1')
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')

    def test_payload_status_is_not_trusted(self):
        payload = {'type': 'charge.completed', 'data': {'checkout_id': 'chk_1', 'status': 'paid'}}
        with mock.patch.object(nomod, 'get_checkout', return_value=self.checkout(status='created')):
            self.post(payload)
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'pending')

    def test_bad_signature_rejected(self):
        body = json.dumps({'type': 'charge.completed', 'data': {'checkout_id': 'chk_1'}})
        response = self.client.post(self.url, body, content_type='application/json',
                                    **sign(body, key=b'wrong-key'))
        self.assertEqual(response.status_code, 401)

    def test_stale_timestamp_rejected(self):
        body = json.dumps({'type': 'charge.completed', 'data': {'checkout_id': 'chk_1'}})
        response = self.client.post(self.url, body, content_type='application/json',
                                    **sign(body, timestamp=int(time.time()) - 600))
        self.assertEqual(response.status_code, 401)


class CheckoutFormTests(TestCase):
    def test_only_cod_when_online_unavailable(self):
        form = CheckoutForm(online_available=False)
        self.assertEqual([c[0] for c in form.fields['payment_method'].choices], ['cod'])

    def test_nomod_and_cod_offered(self):
        form = CheckoutForm(online_available=True)
        self.assertEqual([c[0] for c in form.fields['payment_method'].choices], ['nomod', 'cod'])


class ReconcileCommandTests(NomodTestBase):
    def run_reconcile(self, age_minutes, checkout):
        from datetime import timedelta
        from django.core.management import call_command
        from django.utils import timezone
        Order.objects.filter(pk=self.order.pk).update(created_at=timezone.now() - timedelta(minutes=age_minutes))
        with mock.patch.object(nomod, 'get_checkout', return_value=checkout):
            call_command('reconcile_nomod_payments', stdout=mock.MagicMock())
        self.order.refresh_from_db()

    def test_unpaid_checkout_is_cancelled_after_two_hours(self):
        self.run_reconcile(180, self.checkout(status='enabled'))
        self.assertEqual(self.order.status, 'cancelled')
        self.assertEqual(self.order.payment_status, 'failed')

    def test_recent_unpaid_checkout_is_left_pending(self):
        self.run_reconcile(30, self.checkout(status='enabled'))
        self.assertEqual(self.order.payment_status, 'pending')

    def test_paid_checkout_is_confirmed(self):
        self.run_reconcile(180, self.checkout())
        self.assertEqual(self.order.payment_status, 'paid')

