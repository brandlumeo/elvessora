import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _normalize_phone(phone):
    """Meta's API wants digits only, with country code, no leading +."""
    if not phone:
        return ''
    digits = ''.join(ch for ch in phone if ch.isdigit() or ch == '+')
    digits = digits.lstrip('+')
    return digits if len(digits) >= 8 else ''


def send_whatsapp_message(to_phone, message, template_params=None):
    """Best-effort send via Meta WhatsApp Cloud API — never lets a WhatsApp
    failure break the caller (checkout, signup, admin save, etc.).

    If settings.WHATSAPP_NOTIFICATION_TEMPLATE is set, sends that pre-approved
    template with `message` as its single body parameter — required for
    business-initiated messages (Meta rejects free-form text outside a live
    24h customer chat window). Without a configured template, falls back to
    a free-form text message, which only delivers inside that 24h window
    (e.g. right after the customer messaged the business on WhatsApp).

    Returns True on a successful API call, False otherwise (including when
    WhatsApp isn't configured at all).
    """
    access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
    phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
    if not access_token or not phone_number_id:
        return False

    to = _normalize_phone(to_phone)
    if not to:
        return False

    template_name = getattr(settings, 'WHATSAPP_NOTIFICATION_TEMPLATE', '')
    if template_name:
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'template',
            'template': {
                'name': template_name,
                'language': {'code': getattr(settings, 'WHATSAPP_TEMPLATE_LANGUAGE', 'en_US')},
                'components': [{
                    'type': 'body',
                    'parameters': [{'type': 'text', 'text': p} for p in (template_params or [message])],
                }],
            },
        }
    else:
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {'body': message},
        }

    api_version = getattr(settings, 'WHATSAPP_API_VERSION', 'v20.0')
    url = f'https://graph.facebook.com/{api_version}/{phone_number_id}/messages'

    try:
        response = requests.post(
            url,
            headers={'Authorization': f'Bearer {access_token}'},
            json=payload,
            timeout=10,
        )
        if response.status_code >= 400:
            logger.warning('WhatsApp send to %s failed (%s): %s', to, response.status_code, response.text)
            return False
        return True
    except Exception:
        logger.exception('Failed to send WhatsApp message to %s', to)
        return False
