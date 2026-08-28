"""Tabby (Buy Now, Pay Later) Direct API integration.

Reference: https://docs.tabby.ai/
Flow: create a checkout session -> redirect the customer to Tabby's hosted
checkout_url -> Tabby redirects back to our success/failure/cancel URLs ->
we fetch the payment, verify it is AUTHORIZED, then capture the payment.
"""
import logging
import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class TabbyError(Exception):
    pass


def is_configured():
    return bool(settings.TABBY_PUBLIC_KEY and settings.TABBY_SECRET_KEY)


def _headers(use_secret_key=False):
    token = settings.TABBY_SECRET_KEY if use_secret_key else settings.TABBY_PUBLIC_KEY
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


def _request(method, path, use_secret_key=False, **kwargs):
    url = f'{settings.TABBY_API_BASE_URL}{path}'
    try:
        response = requests.request(method, url, headers=_headers(use_secret_key), timeout=15, **kwargs)
    except requests.RequestException as exc:
        logger.exception('Tabby API request failed: %s %s', method, path)
        raise TabbyError(f'Could not reach Tabby: {exc}') from exc

    if response.status_code >= 400:
        logger.error('Tabby API error %s on %s %s: %s', response.status_code, method, path, response.text)
        raise TabbyError(f'Tabby returned {response.status_code}: {response.text[:300]}')

    return response.json()


def create_checkout_session(order, success_url, failure_url, cancel_url):
    """Creates a Tabby checkout session for an order and returns the
    checkout_url to redirect the customer to. Raises TabbyError on failure.
    """
    currency = 'AED'

    def money(amount):
        return f'{float(amount):.2f}'

    items = []
    for item in order.items.all():
        items.append({
            'title': item.product_name[:256],
            'quantity': item.quantity,
            'unit_price': money(item.unit_price),
            'reference_id': str(item.id),
        })

    shipping_name_parts = (order.shipping_name or 'Customer').split(' ', 1)
    first_name = shipping_name_parts[0]
    last_name = shipping_name_parts[1] if len(shipping_name_parts) > 1 else first_name

    payload = {
        'payment': {
            'amount': money(order.total),
            'currency': currency,
            'description': f'Elvessora order {order.order_number}',
            'buyer': {
                'phone': order.shipping_phone,
                'email': order.guest_email or (order.user.email if order.user_id else ''),
                'name': order.shipping_name,
            },
            'shipping_address': {
                'city': order.shipping_city,
                'address': order.shipping_address[:200],
                'zip': order.shipping_pincode,
            },
            'order': {
                'tax_amount': money(order.tax_amount),
                'shipping_amount': money(order.shipping_charge),
                'discount_amount': money(order.discount_amount),
                'updated_at': timezone.now().isoformat(),
                'reference_id': order.order_number,
                'items': items,
            },
        },
        'lang': 'en',
        'merchant_code': settings.TABBY_MERCHANT_CODE,
        'merchant_urls': {
            'success': success_url,
            'failure': failure_url,
            'cancel': cancel_url,
        },
    }

    # Creating checkout uses Public Key
    data = _request('POST', '/api/v2/checkout', use_secret_key=False, json=payload)
    
    # The URL to redirect to is in configuration.available_products.installments[0].web_url
    # or similar path based on the Tabby response payload.
    # Usually Tabby returns a list of available products (installments, pay later).
    configuration = data.get('configuration', {})
    available_products = configuration.get('available_products', {})
    
    # Find the installments product url
    web_url = ''
    installments = available_products.get('installments', [])
    if installments:
        web_url = installments[0].get('web_url', '')
    
    if not web_url:
        # Fallback to looking in the top level if structure varies
        logger.error('No installments web_url found in Tabby response: %s', data)
        raise TabbyError('Could not retrieve checkout URL from Tabby.')

    return {
        'payment_id': data.get('payment', {}).get('id', ''),
        'checkout_url': web_url,
    }


def get_payment(payment_id):
    """Retrieves payment details. Uses Secret Key."""
    return _request('GET', f'/api/v2/payments/{payment_id}', use_secret_key=True)


def capture_payment(payment_id, amount):
    """Captures an authorized payment. Uses Secret Key."""
    payload = {
        'amount': f'{float(amount):.2f}'
    }
    return _request('POST', f'/api/v1/payments/{payment_id}/captures', use_secret_key=True, json=payload)
