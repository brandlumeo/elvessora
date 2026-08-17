"""Single source of truth for notification/email copy, keyed by notification_type."""
from django.conf import settings

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


def welcome_content(user):
    """Returns (title, message, email_subject, email_body) for a new-account welcome."""
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
    return title, message, subject, body


def order_tracking_url(order):
    return f'{SITE_URL}/orders/tracking/?order_number={order.order_number}'


def order_content(notification_type, order):
    """Returns (title, message, email_subject, email_body) for an order lifecycle event."""
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
        f'Order total: AED {order.total}\n'
        f'Track your order: {order_tracking_url(order)}\n\n'
        '— Elvessora Team'
    )
    return title, message, subject, body
