from decimal import Decimal
from unittest import mock

from django.core.cache import cache
from django.test import TestCase, override_settings

from products.models import Product, ProductVariant

from . import century
from .models import Order, OrderItem


def response(status=200, json_data=None, text=''):
    r = mock.Mock(status_code=status, text=text)
    if json_data is None:
        r.json.side_effect = ValueError
    else:
        r.json.return_value = json_data
    return r


@override_settings(CENTURY_USERNAME='elv', CENTURY_PASSWORD='pw', CENTURY_AUTO_BOOK=False,
                   CENTURY_ITEM_WEIGHT_KG=0.5, CENTURY_API_BASE_URL='https://century.test/api-root/')
class CenturyTestBase(TestCase):
    def setUp(self):
        cache.delete(century.TOKEN_CACHE_KEY)
        product = Product.objects.create(name='Divine Aura', sku='DA', description='x', regular_price=Decimal('300'))
        variant = ProductVariant.objects.create(
            product=product, size='50ml', sku='DA-50', price=Decimal('300'), stock_quantity=10,
        )
        self.order = Order.objects.create(
            guest_email='a@example.com', shipping_name='Sara Ali', shipping_phone='050 123 4567',
            shipping_address='Villa 12, Street 4', shipping_city='Dubai', shipping_state='Dubai',
            shipping_pincode='Al Barsha', subtotal=Decimal('600.00'), total=Decimal('630.00'),
            payment_method='cod', status='confirmed',
        )
        OrderItem.objects.create(
            order=self.order, product=product, variant=variant, product_name='Divine Aura',
            variant_size='50ml', quantity=3, unit_price=Decimal('200.00'),
        )


class CenturyPayloadTests(CenturyTestBase):
    def test_cod_payload(self):
        p = century.consignment_payload(self.order)
        self.assertEqual(p['BookingRefNo'], self.order.order_number)
        self.assertEqual(p['Address'], 'Villa 12, Street 4, Dubai, Al Barsha')
        self.assertEqual(p['Weight'], 1.5)
        self.assertTrue(p['Isdomestic'])
        self.assertEqual(p['Country'], 'UNITED ARAB EMIRATES')
        self.assertIn('CASH ON DELIVERY: collect AED 630.00', p['SplInstruction'])

    def test_prepaid_payload(self):
        self.order.payment_method = 'nomod'
        self.order.payment_status = 'paid'
        self.assertIn('Prepaid', century.consignment_payload(self.order)['SplInstruction'])

    def test_add_response_parsing(self):
        self.assertEqual(century._parse_add_response('true, 75337954'), '75337954')
        self.assertEqual(century._parse_add_response('"true, 75337954"'), '75337954')
        with self.assertRaises(century.CenturyError):
            century._parse_add_response('false, Invalid city')


class CenturyApiTests(CenturyTestBase):
    @mock.patch('orders.century.requests.request')
    @mock.patch('orders.century.requests.post')
    def test_book_logs_in_and_records_tracking(self, post, request):
        post.return_value = response(json_data={'token': {'access_token': 'tok1', 'Error': None}})
        request.return_value = response(json_data='true, 75337954')
        self.assertEqual(century.book_consignment(self.order), '75337954')
        self.order.refresh_from_db()
        self.assertEqual(self.order.tracking_number, '75337954')
        self.assertEqual(self.order.courier_name, 'Century Express')
        self.assertEqual(request.call_args.kwargs['headers']['Authorization'], 'Bearer tok1')
        self.assertEqual(request.call_args.args[1], 'https://century.test/api-root/api/OperationAPI/AddConsignmentAPI')
        # Booking twice does not create a second consignment
        century.book_consignment(self.order)
        self.assertEqual(request.call_count, 1)

    @mock.patch('orders.century.requests.request')
    @mock.patch('orders.century.requests.post')
    def test_expired_token_logs_in_again(self, post, request):
        cache.set(century.TOKEN_CACHE_KEY, 'old')
        post.return_value = response(json_data={'token': {'access_token': 'new', 'Error': None}})
        request.side_effect = [response(status=401, text='expired'), response(json_data='true, 1')]
        century.book_consignment(self.order)
        self.assertEqual(request.call_args.kwargs['headers']['Authorization'], 'Bearer new')

    @mock.patch('orders.century.requests.post')
    def test_login_error_raises(self, post):
        post.return_value = response(json_data={'token': {'access_token': None, 'Error': 'Invalid user'}})
        with self.assertRaises(century.CenturyError):
            century.book_consignment(self.order)


class CenturyStatusTests(CenturyTestBase):
    def test_status_mapping(self):
        self.assertEqual(century.order_status_for('Picked Up'), 'shipped')
        self.assertEqual(century.order_status_for('In Transit'), 'shipped')
        self.assertEqual(century.order_status_for('Out For Delivery'), 'out_for_delivery')
        self.assertEqual(century.order_status_for('DELIVERED'), 'delivered')
        self.assertIsNone(century.order_status_for('Undelivered - customer not available'))
        self.assertIsNone(century.order_status_for('Return to origin'))
        self.assertIsNone(century.order_status_for('Booked'))

    def sync(self, status_text):
        self.order.tracking_number = '75337954'
        self.order.courier_name = century.COURIER_NAME
        self.order.save()
        # Wrapper key spelled as in Century's UAT document
        details = {'ConsignmnentDetails': {
            'consignmentid': 3023682, 'consignmentnumber': '75337954', 'ServiceType': 'CREDIT',
            'totalweight': 0.0, 'Status': status_text,
        }}
        with mock.patch.object(century, '_request', return_value=details) as req:
            text = century.sync_order(self.order)
        self.assertEqual(req.call_args.kwargs['params']['ConsignmentNumber'], '75337954')
        self.order.refresh_from_db()
        return text

    def test_delivered_moves_order_forward(self):
        self.assertEqual(self.sync('Delivered'), 'Delivered')
        self.assertEqual(self.order.status, 'delivered')
        self.assertEqual(self.order.century_status, 'Delivered')
        self.assertIsNotNone(self.order.century_synced_at)

    def test_never_moves_backward(self):
        self.order.status = 'delivered'
        self.sync('In Transit')
        self.assertEqual(self.order.status, 'delivered')
        self.assertEqual(self.order.century_status, 'In Transit')

    def test_status_found_in_nested_history(self):
        details = {'consignmentnumber': '1', 'TrackingHistory': [
            {'StatusName': 'Picked Up'}, {'StatusName': 'Out For Delivery'},
        ]}
        self.assertEqual(century.status_text(details), 'Out For Delivery')

    def test_cancelled_order_untouched(self):
        self.order.status = 'cancelled'
        self.sync('Delivered')
        self.assertEqual(self.order.status, 'cancelled')


class CenturyAutoBookTests(CenturyTestBase):
    @override_settings(CENTURY_AUTO_BOOK=True)
    def test_confirming_an_order_books_it(self):
        self.order.status = 'pending'
        self.order.save()
        with mock.patch.object(century, '_request', return_value='true, 555') as req, \
                self.captureOnCommitCallbacks(execute=True):
            self.order.status = 'confirmed'
            self.order.save()
        req.assert_called_once()
        self.order.refresh_from_db()
        self.assertEqual(self.order.tracking_number, '555')

    @override_settings(CENTURY_AUTO_BOOK=True)
    def test_booking_failure_does_not_break_the_order(self):
        self.order.status = 'pending'
        self.order.save()
        with mock.patch.object(century, '_request', side_effect=century.CenturyError('down')), \
                self.captureOnCommitCallbacks(execute=True):
            self.order.status = 'confirmed'
            self.order.save()
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(self.order.tracking_number, '')
