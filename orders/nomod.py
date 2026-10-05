"""Nomod Hosted Checkout integration.

Reference: https://nomod.com/docs/api-reference/create-checkout
Flow: create a checkout for an order -> redirect the customer to Nomod's
hosted page (cards, Apple Pay, Google Pay, Tabby, Tamara) -> Nomod redirects
back to our success/failure/cancelled URL -> we re-fetch the checkout from
Nomod and only mark the order paid if Nomod says it is paid for exactly this
order's amount, currency and reference. The redirect itself is never trusted.

Webhooks (charge.* events) are signed Svix-style; see
https://nomod.com/docs/webhooks/verifying-webhook-signatures
"""
import base64
import hashlib
import hmac
import logging
import re
import time
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

CURRENCY = 'AED'
CENT = Decimal('0.01')
WEBHOOK_TOLERANCE_SECONDS = 5 * 60

# Checkout statuses. The API reference lists created/paid/cancelled/expired,
# but the live API returns 'enabled' for a new, unpaid checkout, so both are
# treated as "not paid yet". Anything unrecognised is logged (see views).
STATUS_CREATED = 'created'
STATUS_ENABLED = 'enabled'
STATUS_PAID = 'paid'
STATUS_CANCELLED = 'cancelled'
STATUS_EXPIRED = 'expired'
KNOWN_STATUSES = {STATUS_CREATED, STATUS_ENABLED, STATUS_PAID, STATUS_CANCELLED, STATUS_EXPIRED}


class NomodError(Exception):
    pass


def is_configured():
    return bool(settings.NOMOD_API_KEY)


def _money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def _request(method, path, **kwargs):
    url = f'{settings.NOMOD_API_BASE_URL.rstrip("/")}{path}'
    headers = {
        'X-API-KEY': settings.NOMOD_API_KEY,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    try:
        response = requests.request(method, url, headers=headers, timeout=15, **kwargs)
    except requests.RequestException as exc:
        logger.exception('Nomod API request failed: %s %s', method, path)
        raise NomodError(f'Could not reach Nomod: {exc}') from exc

    if response.status_code >= 400:
        logger.error('Nomod API error %s on %s %s: %s', response.status_code, method, path, response.text)
        raise NomodError(f'Nomod returned {response.status_code}: {response.text[:300]}')

    try:
        return response.json()
    except ValueError as exc:
        raise NomodError('Nomod returned a non-JSON response.') from exc


def _e164_phone(raw):
    """Best-effort UAE phone normalisation to E.164 (Nomod rejects other
    formats). Returns '' when it can't produce a plausible number, so the
    field is simply left out rather than failing the checkout."""
    digits = re.sub(r'\D', '', raw or '')
    if (raw or '').strip().startswith('+'):
        candidate = digits
    elif digits.startswith('00'):
        candidate = digits[2:]
    elif digits.startswith('971'):
        candidate = digits
    elif digits.startswith('0'):
        candidate = '971' + digits[1:]
    else:
        candidate = '971' + digits
    return f'+{candidate}' if 8 <= len(candidate) <= 15 else ''


def _items(order, amount):
    """Line items whose totals, minus the order discount, add up to exactly
    `amount`. Shipping and VAT are sent as their own lines; the VAT line is
    derived from the rounded total so rounding can never make them disagree.
    """
    lines = []
    for item in order.items.all():
        unit = _money(item.unit_price)
        line_total = _money(unit * item.quantity)
        lines.append({
            'item_id': str(item.pk),
            'name': f'{item.product_name} ({item.variant_size})' if item.variant_size else item.product_name,
            'quantity': item.quantity,
            'unit_amount': str(unit),
            'total_amount': str(line_total),
            'net_amount': str(line_total),
        })
        if item.gift_wrapping:
            wrap = _money(item.line_total - item.unit_price * item.quantity)
            lines.append({
                'item_id': f'{item.pk}-wrap',
                'name': 'Gift wrapping',
                'quantity': 1,
                'unit_amount': str(wrap),
                'total_amount': str(wrap),
                'net_amount': str(wrap),
            })

    shipping = _money(order.shipping_charge)
    if shipping > 0:
        lines.append({
            'item_id': 'shipping', 'name': 'Shipping', 'quantity': 1,
            'unit_amount': str(shipping), 'total_amount': str(shipping), 'net_amount': str(shipping),
        })

    discount = _money(order.discount_amount)
    goods = sum((Decimal(line['total_amount']) for line in lines), Decimal('0'))
    vat = amount + discount - goods
    if vat > 0:
        lines.append({
            'item_id': 'vat', 'name': 'VAT', 'quantity': 1,
            'unit_amount': str(vat), 'total_amount': str(vat), 'net_amount': str(vat),
        })
    return lines


def create_checkout(order, success_url, failure_url, cancelled_url):
    """Creates a Nomod hosted checkout for an order. Returns
    {'checkout_id', 'checkout_url'}; raises NomodError on failure."""
    amount = _money(order.total)
    name_parts = (order.shipping_name or '').strip().split(None, 1)
    customer = {'email': order.guest_email or (order.user.email if order.user_id else '')}
    # Nomod rejects customer details without both a first and last name, so
    # for a single-word name no details are prefilled and the customer types
    # them on Nomod's page, rather than seeing the name twice ("Akash Akash").
    if len(name_parts) == 2:
        customer['first_name'], customer['last_name'] = name_parts
    phone = _e164_phone(order.shipping_phone)
    if phone:
        customer['phone_number'] = phone

    payload = {
        'reference_id': order.order_number,
        'amount': str(amount),
        'currency': CURRENCY,
        'items': _items(order, amount),
        'success_url': success_url,
        'failure_url': failure_url,
        'cancelled_url': cancelled_url,
        'metadata': {'order': order.order_number},
    }
    discount = _money(order.discount_amount)
    if discount > 0:
        payload['discount'] = str(discount)
    if 'first_name' in customer:
        payload['customer'] = customer

    data = _request('POST', '/v1/checkout', json=payload)
    checkout_id = data.get('id', '')
    checkout_url = data.get('url', '')
    if not checkout_id or not checkout_url:
        logger.error('Nomod checkout response missing id/url: %s', data)
        raise NomodError('Could not retrieve checkout URL from Nomod.')
    return {'checkout_id': checkout_id, 'checkout_url': checkout_url}


def get_checkout(checkout_id):
    return _request('GET', f'/v1/checkout/{checkout_id}')


def is_paid_for_order(checkout, order):
    """True only if Nomod reports this checkout as paid for exactly this
    order: same reference, AED, and the full order total."""
    if (checkout.get('status') or '').lower() != STATUS_PAID:
        return False
    if checkout.get('reference_id') != order.order_number:
        logger.error('Nomod checkout %s reference %r != order %s',
                     checkout.get('id'), checkout.get('reference_id'), order.order_number)
        return False
    if (checkout.get('currency') or '').upper() != CURRENCY:
        logger.error('Nomod checkout %s currency %r != AED', checkout.get('id'), checkout.get('currency'))
        return False
    try:
        paid_amount = _money(str(checkout.get('amount')))
    except (InvalidOperation, TypeError):
        return False
    if paid_amount != _money(order.total):
        logger.error('Nomod checkout %s amount %s != order %s total %s',
                     checkout.get('id'), paid_amount, order.order_number, order.total)
        return False
    return True


def verify_webhook_signature(headers, raw_body, now=None):
    """Verifies a Nomod (Svix) webhook signature against the raw request
    body. `headers` is a mapping with svix-id / svix-timestamp /
    svix-signature. Rejects anything older or newer than five minutes."""
    secret = settings.NOMOD_WEBHOOK_SECRET
    msg_id = headers.get('svix-id', '')
    timestamp = headers.get('svix-timestamp', '')
    signature_header = headers.get('svix-signature', '')
    if not (secret and msg_id and timestamp and signature_header):
        return False

    try:
        ts = int(timestamp)
    except ValueError:
        return False
    if abs((now if now is not None else time.time()) - ts) > WEBHOOK_TOLERANCE_SECONDS:
        return False

    try:
        key = base64.b64decode(secret.split('_', 1)[1] if secret.startswith('whsec_') else secret)
    except (ValueError, IndexError):
        logger.error('NOMOD_WEBHOOK_SECRET is not a valid whsec_ secret.')
        return False

    body = raw_body.decode('utf-8') if isinstance(raw_body, bytes) else raw_body
    signed = f'{msg_id}.{timestamp}.{body}'.encode('utf-8')
    expected = base64.b64encode(hmac.new(key, signed, hashlib.sha256).digest()).decode()

    # The header may carry several space-separated "v1,<sig>" entries.
    for part in signature_header.split():
        version, _, sig = part.partition(',')
        if version == 'v1' and hmac.compare_digest(sig, expected):
            return True
    return False
