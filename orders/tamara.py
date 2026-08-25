"""Tamara (Buy Now, Pay Later) Direct API integration.

Reference: https://docs.tamara.co/reference/createcheckoutsession
Flow: create a checkout session -> redirect the customer to Tamara's hosted
checkout_url -> Tamara redirects back to our success/failure/cancel URLs ->
we fetch the order, authorise it, then capture the payment.

Every function is a thin, explicit wrapper around one Tamara endpoint —
no retries or queuing, matching the synchronous style of the existing
Razorpay checkout flow. Raises TamaraError on any failure; callers decide
how to present that to the shopper.
"""
import logging

import jwt
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TamaraError(Exception):
    pass


def is_configured():
    return bool(settings.TAMARA_API_TOKEN and settings.TAMARA_NOTIFICATION_TOKEN)


def _headers():
    return {
        'Authorization': f'Bearer {settings.TAMARA_API_TOKEN}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


def _request(method, path, **kwargs):
    url = f'{settings.TAMARA_API_BASE_URL}{path}'
    try:
        response = requests.request(method, url, headers=_headers(), timeout=15, **kwargs)
    except requests.RequestException as exc:
        logger.exception('Tamara API request failed: %s %s', method, path)
        raise TamaraError(f'Could not reach Tamara: {exc}') from exc

    if response.status_code >= 400:
        logger.error('Tamara API error %s on %s %s: %s', response.status_code, method, path, response.text)
        raise TamaraError(f'Tamara returned {response.status_code}: {response.text[:300]}')

    return response.json()


def create_checkout_session(order, success_url, failure_url, cancel_url):
    """Creates a Tamara checkout session for an order and returns the
    checkout_url to redirect the customer to. Raises TamaraError on failure.
    Expects order.items (OrderItem rows) to already be saved.
    """
    currency = 'AED'

    def money(amount):
        return {'amount': float(amount), 'currency': currency}

    items = []
    for item in order.items.all():
        items.append({
            'reference_id': str(item.id),
            'type': 'Physical',
            'name': item.product_name[:256],
            'sku': (item.variant.sku if item.variant_id else 'N/A'),
            'quantity': item.quantity,
            'total_amount': money(item.line_total),
        })

    shipping_name_parts = (order.shipping_name or 'Customer').split(' ', 1)
    first_name = shipping_name_parts[0]
    last_name = shipping_name_parts[1] if len(shipping_name_parts) > 1 else first_name

    payload = {
        'order_reference_id': order.order_number,
        'total_amount': money(order.total),
        'description': f'Elvessora order {order.order_number}',
        'country_code': settings.TAMARA_COUNTRY_CODE,
        'payment_type': 'PAY_BY_INSTALMENTS',
        'instalments': 3,
        'items': items,
        'consumer': {
            'first_name': first_name,
            'last_name': last_name,
            'phone_number': order.shipping_phone,
            'email': order.guest_email or (order.user.email if order.user_id else ''),
        },
        'shipping_address': {
            'first_name': first_name,
            'last_name': last_name,
            'line1': order.shipping_address[:200],
            'city': order.shipping_city,
            'country_code': settings.TAMARA_COUNTRY_CODE,
        },
        'tax_amount': money(order.tax_amount),
        'shipping_amount': money(order.shipping_charge),
        'merchant_url': {
            'success': success_url,
            'failure': failure_url,
            'cancel': cancel_url,
        },
    }

    data = _request('POST', '/checkout', json=payload)
    return {
        'checkout_id': data.get('checkout_id', ''),
        'order_id': data.get('order_id', ''),
        'checkout_url': data.get('checkout_url', ''),
    }


def get_order(tamara_order_id):
    return _request('GET', f'/orders/{tamara_order_id}')


def authorise_order(tamara_order_id):
    return _request('POST', f'/orders/{tamara_order_id}/authorise')


def capture_order(tamara_order_id, total_amount, shipping_company='Elvessora'):
    """Captures payment for an authorised order. In Tamara's recommended
    flow this is called once the order actually ships; this integration
    calls it immediately after authorisation instead, for the same
    "capture at checkout" simplicity as the existing Razorpay flow. If you
    later want to hold funds until fulfillment, move this call to wherever
    the order status is set to 'shipped' instead.
    """
    from django.utils import timezone

    payload = {
        'order_id': tamara_order_id,
        'total_amount': {'amount': float(total_amount), 'currency': 'AED'},
        'shipping_info': {
            'shipped_at': timezone.now().isoformat(),
            'shipping_company': shipping_company,
        },
    }
    return _request('POST', '/payments/capture', json=payload)


def verify_notification_token(token):
    """Verifies a webhook's tamaraToken (HS256 JWT signed with the
    Notification Token). Returns the decoded payload, or None if invalid.
    """
    if not token or not settings.TAMARA_NOTIFICATION_TOKEN:
        return None
    try:
        return jwt.decode(token, settings.TAMARA_NOTIFICATION_TOKEN, algorithms=['HS256'])
    except jwt.PyJWTError:
        logger.warning('Rejected Tamara webhook with invalid token')
        return None
