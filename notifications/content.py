"""Single source of truth for notification/email copy, keyed by notification_type."""
from django.conf import settings
from django.template.loader import render_to_string

from .emailer import LOGO_CID

SITE_URL = getattr(settings, 'SITE_URL', 'https://www.elvessora.ae').rstrip('/')

ORDER_EVENT_COPY = {
    'order_placed': (
        'Order Placed',
        "We've received your order {order_number} and it's being reviewed.",
    ),
    'order_confirmed': (
        'Order Confirmed',
        'Your order {order_number} has been confirmed and will be prepared for shipping.',
    ),
    'order_processing': (
        'Order Processing',
        'Your order {order_number} is now being processed.',
    ),
    'order_shipped': (
        'Order Shipped',
        'Your order {order_number} has shipped{tracking_suffix}.',
    ),
    'order_out_for_delivery': (
        'Out for Delivery',
        'Your order {order_number} is out for delivery and should arrive soon.',
    ),
    'order_delivered': (
        'Order Delivered',
        'Your order {order_number} has been delivered. We hope you love it!',
    ),
    'order_cancelled': (
        'Order Cancelled',
        'Your order {order_number} has been cancelled.',
    ),
    'order_refunded': (
        'Order Refunded',
        'A refund has been processed for your order {order_number}.',
    ),
}


def _display_name(user):
    return user.first_name or user.username


def _site_context():
    """Common template context shared by every email: brand/contact info and
    the Content-ID the logo is embedded under (see emailer.py) — inline
    cid: references always render, unlike a remote image URL some email
    clients' image proxies may fail to fetch."""
    from core.models import SiteSettings
    site = SiteSettings.get()
    return {
        'site': site,
        'site_url': SITE_URL,
        'logo_cid': LOGO_CID,
    }


def welcome_content(user):
    """Returns (title, message, email_subject, email_body, email_html) for a new-account welcome."""
    name = _display_name(user)
    title = 'Welcome to Elvessora!'
    message = (
        f'Hi {name}, your account has been created successfully. '
        'Explore our latest fragrances and enjoy a personalised shopping experience.'
    )
    subject = 'Welcome to Elvessora'
    body = (
        f'Hi {name},\n\n'
        'Welcome to Elvessora! Your account has been created successfully.\n\n'
        f'Start exploring our fragrances: {SITE_URL}/\n\n'
        '— Elvessora Team'
    )
    html = render_to_string('emails/welcome_email.html', {**_site_context(), 'name': name})
    return title, message, subject, body, html


def login_alert_content(user, ip_address, device, when):
    """Returns (title, message, email_subject, email_body, email_html) for a new-device/location login."""
    name = _display_name(user)
    where = ip_address or 'an unknown location'
    when_str = when.strftime('%b %d, %Y at %I:%M %p UTC')
    title = 'New Login Detected'
    message = f'New sign-in to your account from {where} on {device} — {when_str}.'
    subject = 'New login to your Elvessora account'
    body = (
        f'Hi {name},\n\n'
        f'We noticed a new sign-in to your Elvessora account.\n\n'
        f'When: {when_str}\n'
        f'Device: {device}\n'
        f'IP address: {where}\n\n'
        "If this was you, no action is needed. If you don't recognise this activity, "
        f'reset your password immediately: {SITE_URL}/accounts/password-reset/\n\n'
        '— Elvessora Team'
    )
    html = render_to_string('emails/login_alert_email.html', {
        **_site_context(),
        'name': name, 'where': where, 'device': device, 'when_str': when_str,
    })
    return title, message, subject, body, html


def order_tracking_url(order):
    return f'{SITE_URL}/orders/tracking/?order_number={order.order_number}'


def order_content(notification_type, order):
    """Returns (title, message, email_subject, email_body, email_html) for an order lifecycle event."""
    title, message_template = ORDER_EVENT_COPY[notification_type]

    tracking_suffix = ''
    if order.tracking_number:
        tracking_suffix = f' — tracking number {order.tracking_number}'
        if order.courier_name:
            tracking_suffix += f' via {order.courier_name}'

    message = message_template.format(order_number=order.order_number, tracking_suffix=tracking_suffix)
    subject = f'{title} — {order.order_number}'
    body = (
        f'Hi {order.shipping_name},\n\n'
        f'{message}\n\n'
        f'Order total: AED {order.total:.2f}\n'
        f'Track your order: {order_tracking_url(order)}\n\n'
        '— Elvessora Team'
    )
    html = render_to_string('emails/order_notification.html', {
        **_site_context(),
        'title': title,
        'message': message,
        'order': order,
        'items': order.items.all(),
        'tracking_url': order_tracking_url(order),
    })
    return title, message, subject, body, html
