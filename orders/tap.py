"""Tap Payments (cards, Apple Pay, mada, etc.) Direct API integration.

Reference: https://developers.tap.company/reference/create-a-charge
Flow: create a charge -> redirect the customer to Tap's hosted
transaction.url -> Tap redirects back to our single return URL ->
we fetch the charge and check its status. Unlike Tamara/Tabby there is
no separate authorise/capture step: the charge is created with
auto-capture, so a CAPTURED status on return means payment is done.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class TapError(Exception):
    pass


def is_configured():
    return bool(settings.TAP_SECRET_KEY)


def _headers():
    return {
        'Authorization': f'Bearer {settings.TAP_SECRET_KEY}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }


def _request(method, path, **kwargs):
    url = f'{settings.TAP_API_BASE_URL}{path}'
    try:
        response = requests.request(method, url, headers=_headers(), timeout=15, **kwargs)
    except requests.RequestException as exc:
        logger.exception('Tap API request failed: %s %s', method, path)
        raise TapError(f'Could not reach Tap: {exc}') from exc

    if response.status_code >= 400:
        logger.error('Tap API error %s on %s %s: %s', response.status_code, method, path, response.text)
        raise TapError(f'Tap returned {response.status_code}: {response.text[:300]}')

    return response.json()


def create_charge(order, redirect_url, webhook_url=''):
    """Creates a Tap charge for an order and returns the checkout_url to
    redirect the customer to. Raises TapError on failure.
    """
    shipping_name_parts = (order.shipping_name or 'Customer').split(' ', 1)
    first_name = shipping_name_parts[0]
    last_name = shipping_name_parts[1] if len(shipping_name_parts) > 1 else first_name

    payload = {
        'amount': float(order.total),
        'currency': 'AED',
        'threeDSecure': True,
        'save_card': False,
        'description': f'Elvessora order {order.order_number}',
        'reference': {'order': order.order_number},
        'customer': {
            'first_name': first_name,
            'last_name': last_name,
            'email': order.guest_email or (order.user.email if order.user_id else ''),
            'phone': {
                'country_code': '971',
                'number': (order.shipping_phone or '').lstrip('+').lstrip('971'),
            },
        },
        'source': {'id': 'src_all'},
        'redirect': {'url': redirect_url},
    }
    if webhook_url:
        payload['post'] = {'url': webhook_url}

    data = _request('POST', '/charges', json=payload)
    checkout_url = data.get('transaction', {}).get('url', '')
    if not checkout_url:
        logger.error('No transaction.url found in Tap response: %s', data)
        raise TapError('Could not retrieve checkout URL from Tap.')

    return {
        'charge_id': data.get('id', ''),
        'checkout_url': checkout_url,
    }


def get_charge(charge_id):
    return _request('GET', f'/charges/{charge_id}')
