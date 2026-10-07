"""Century Express courier integration.

Reference: "Century API Integration Documentation - UAT" (Century Express,
2026). Flow: log in for a bearer token (valid 90 days; logging in again
returns the same token until it expires) -> add a consignment for an order,
which returns Century's consignment number -> poll the consignment status
(Century has no webhooks) and move the order along as the parcel travels.

The document does not cover shipping labels, a cash-on-delivery amount
field, COD remittance, or the list of status values, so:
  - COD orders send the amount to collect in the special instructions;
  - statuses are matched on keywords and the raw text is kept on the order
    (century_status) so staff can always see what Century said.
"""
import json
import logging
import re
from decimal import Decimal

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

COURIER_NAME = 'Century Express'
TOKEN_CACHE_KEY = 'century_express_token'
TOKEN_CACHE_SECONDS = 24 * 60 * 60   # re-check daily; Century keeps it for 90 days

# Order statuses a parcel moves through, in order. Century can only move an
# order forward along this list, never back, and never touches cancelled or
# refunded orders.
PROGRESSION = ['pending', 'confirmed', 'processing', 'shipped', 'out_for_delivery', 'delivered']

# Keys the status response might keep the status text under (the UAT document
# only shows the start of the response, so match a few likely names).
STATUS_KEYS = (
    'status', 'currentstatus', 'consignmentstatus', 'laststatus',
    'statusname', 'trackingstatus', 'statusdescription',
)


class CenturyError(Exception):
    pass


def is_configured():
    return bool(settings.CENTURY_USERNAME and settings.CENTURY_PASSWORD)


def _url(path):
    return f'{settings.CENTURY_API_BASE_URL.rstrip("/")}/{path.lstrip("/")}'


def _login():
    try:
        response = requests.post(
            _url('api/Login/Login'),
            json={'username': settings.CENTURY_USERNAME, 'password': settings.CENTURY_PASSWORD},
            timeout=15,
        )
    except requests.RequestException as exc:
        logger.exception('Century Express login request failed')
        raise CenturyError(f'Could not reach Century Express: {exc}') from exc
    if response.status_code >= 400:
        logger.error('Century Express login error %s: %s', response.status_code, response.text)
        raise CenturyError(f'Century Express login failed ({response.status_code}).')
    try:
        token = response.json().get('token') or {}
    except ValueError as exc:
        raise CenturyError('Century Express login returned a non-JSON response.') from exc
    if token.get('Error') or not token.get('access_token'):
        raise CenturyError(f'Century Express login failed: {token.get("Error") or "no token returned"}')
    cache.set(TOKEN_CACHE_KEY, token['access_token'], TOKEN_CACHE_SECONDS)
    return token['access_token']


def _request(method, path, **kwargs):
    """Calls the API with the cached token, logging in again once if Century
    says the token is no longer valid."""
    token = cache.get(TOKEN_CACHE_KEY) or _login()
    for attempt in (1, 2):
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        try:
            response = requests.request(method, _url(path), headers=headers, timeout=15, **kwargs)
        except requests.RequestException as exc:
            logger.exception('Century Express request failed: %s %s', method, path)
            raise CenturyError(f'Could not reach Century Express: {exc}') from exc
        if response.status_code == 401 and attempt == 1:
            cache.delete(TOKEN_CACHE_KEY)
            token = _login()
            continue
        break
    if response.status_code >= 400:
        logger.error('Century Express error %s on %s %s: %s', response.status_code, method, path, response.text)
        raise CenturyError(f'Century Express returned {response.status_code}: {response.text[:300]}')
    try:
        return response.json()
    except ValueError:
        return response.text


def _weight_kg(order):
    pieces = sum(item.quantity for item in order.items.all()) or 1
    return max(Decimal('0.5'), Decimal(str(settings.CENTURY_ITEM_WEIGHT_KG)) * pieces)


def consignment_payload(order):
    is_domestic = order.shipping_country.strip().lower() in ('united arab emirates', 'uae', 'ae')
    address = ', '.join(part for part in (
        order.shipping_address.strip(), order.shipping_state.strip(), order.shipping_pincode.strip(),
    ) if part)
    instructions = [f'Elvessora order {order.order_number}']
    if order.payment_method == 'cod' and order.payment_status != 'paid':
        instructions.append(f'CASH ON DELIVERY: collect AED {order.total}')
    else:
        instructions.append('Prepaid - do not collect cash')
    return {
        'BookingRefNo': order.order_number,
        'ContactName': order.shipping_name,
        'ContactNumber': order.shipping_phone,
        'Address': address,
        'City': order.shipping_city,
        'Weight': float(_weight_kg(order)),
        'Isdomestic': is_domestic,
        'Pieces': 1,
        'MaterialCost': float(order.total),
        'SplInstruction': '. '.join(instructions),
        'Country': order.shipping_country.upper(),
    }


def _parse_add_response(result):
    """Century answers Add Consignment with a string like "true, 75337954";
    on failure the second part is the reason."""
    text = result if isinstance(result, str) else json.dumps(result)
    text = text.strip().strip('"').strip()
    ok, _, rest = text.partition(',')
    rest = rest.strip().strip('"').strip()
    if ok.strip().lower() == 'true' and rest:
        return rest
    raise CenturyError(f'Century Express did not accept the consignment: {text[:300]}')


def book_consignment(order):
    """Books the order with Century Express and records the consignment
    number as its tracking number. Returns the consignment number."""
    if not is_configured():
        raise CenturyError('Century Express is not configured.')
    if order.courier_name == COURIER_NAME and order.tracking_number:
        return order.tracking_number
    number = _parse_add_response(
        _request('POST', 'api/OperationAPI/AddConsignmentAPI', json=consignment_payload(order))
    )
    order.tracking_number = number
    order.courier_name = COURIER_NAME
    order.century_status = 'Booked'
    order.century_synced_at = timezone.now()
    order.save(update_fields=['tracking_number', 'courier_name', 'century_status', 'century_synced_at', 'updated_at'])
    logger.info('Booked order %s with Century Express as %s', order.order_number, number)
    return number


def get_consignment(number):
    result = _request(
        'GET', 'api/OperationAPI/getconsignmentstatus',
        params={'ConsignmentNumber': number, 'supplierawbno': '', 'alternateconsignmentnumber': ''},
    )
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except ValueError:
            raise CenturyError(f'Unexpected status response: {result[:300]}')
    if not isinstance(result, dict):
        return {}
    # Century spells the wrapper "ConsignmnentDetails" in its UAT document;
    # match any spelling so a later fix on their side doesn't break this.
    for key, value in result.items():
        if isinstance(value, dict) and key.lower().startswith('consign') and 'detail' in key.lower():
            return value
    return result


def status_text(details):
    """The status text from a status response, searching nested objects too
    (the UAT document cuts off before the status field)."""
    for key, value in details.items():
        if key.lower() in STATUS_KEYS and isinstance(value, str) and value.strip():
            return value.strip()
    for value in details.values():
        nested = [value] if isinstance(value, dict) else (value if isinstance(value, list) else [])
        for item in reversed(nested):   # tracking histories usually end with the latest event
            if isinstance(item, dict):
                text = status_text(item)
                if text:
                    return text
    return ''


def order_status_for(text):
    """Maps Century's status text to an order status, or None when it isn't a
    step the order should move to on its own (e.g. returns, failed attempts)."""
    t = re.sub(r'[^a-z ]', ' ', text.lower())
    if not t.strip():
        return None
    if re.search(r'\b(return|rto|cancel|undeliver|not deliver|attempt|refused|hold)', t):
        return None
    if 'out for delivery' in t or re.search(r'\bofd\b', t):
        return 'out_for_delivery'
    if 'deliver' in t:
        return 'delivered'
    if re.search(r'\b(picked|pickup done|in transit|transit|dispatch|shipped|checked in|received|arrived|forward)', t):
        return 'shipped'
    return None


def sync_order(order):
    """Fetches the consignment's status and applies it. Returns the status
    text Century reported."""
    details = get_consignment(order.tracking_number)
    text = status_text(details)
    if not text:
        logger.warning('No status field found for Century consignment %s: %s', order.tracking_number, details)
    order.century_status = (text or 'Unknown')[:100]
    order.century_synced_at = timezone.now()
    fields = ['century_status', 'century_synced_at', 'updated_at']
    target = order_status_for(text)
    if (target and order.status in PROGRESSION
            and PROGRESSION.index(target) > PROGRESSION.index(order.status)):
        order.status = target
        fields.append('status')
    # Order's save signals still run with update_fields, so a status change
    # here sends the customer the usual shipped/delivered notification.
    order.save(update_fields=fields)
    return text
