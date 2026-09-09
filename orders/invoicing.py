"""Order invoice PDF generation.

Uses xhtml2pdf (pure-Python, no system-level dependencies like wkhtmltopdf
or Cairo/Pango) so it installs cleanly via pip alone on both local dev and
the production host.
"""
import io
import logging

from django.template.loader import render_to_string
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)


def render_invoice_pdf(order):
    """Renders the invoice for an order to PDF bytes. Returns None on failure
    (logged) rather than raising, so a broken invoice never blocks the
    payment-confirmation flow that triggers it."""
    from core.models import SiteSettings
    site = SiteSettings.get()

    html = render_to_string('orders/invoice_pdf.html', {'order': order, 'site': site})

    buffer = io.BytesIO()
    result = pisa.CreatePDF(src=html, dest=buffer)
    if result.err:
        logger.error('Failed to render invoice PDF for order %s (%d errors)', order.order_number, result.err)
        return None

    return buffer.getvalue()


def send_invoice_email(order):
    """Emails the order's invoice as a PDF attachment to the customer.
    Called once, the moment payment_status first becomes 'paid' — see
    notifications/signals.py. Best-effort: a failure here is logged but
    never raised, since it must not break the payment-confirmation flow
    that triggers it.
    """
    to_email = order.user.email if order.user_id else order.guest_email
    if not to_email:
        return

    try:
        from notifications.content import order_tracking_url, _site_context
        from notifications.emailer import send_notification_email

        pdf_bytes = render_invoice_pdf(order)
        if pdf_bytes is None:
            return

        html_body = render_to_string('emails/invoice_email.html', {
            **_site_context(),
            'order': order,
            'tracking_url': order_tracking_url(order),
        })
        body = (
            f'Hi {order.shipping_name},\n\n'
            f"We've received your payment for order {order.order_number}. "
            'Your invoice is attached as a PDF.\n\n'
            f'Amount paid: AED {order.total:.2f}\n'
            f'Track your order: {order_tracking_url(order)}\n\n'
            '— Elvessora Team'
        )

        send_notification_email(
            to_email,
            f'Your Invoice — {order.order_number}',
            body,
            html_body,
            attachments=[(f'Invoice-{order.order_number}.pdf', pdf_bytes, 'application/pdf')],
        )
    except Exception:
        logger.exception('Failed to send invoice email for order %s', order.order_number)
