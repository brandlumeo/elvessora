import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail

logger = logging.getLogger(__name__)


def send_notification_email(to_email, subject, body, html_body=None):
    """Best-effort send — never lets an email failure break the caller (checkout, admin save, etc.).

    Sends a proper HTML email (with the plain-text body as the fallback
    alternative for clients that don't render HTML) when html_body is given;
    falls back to a plain-text-only send otherwise.
    """
    if not to_email:
        return
    try:
        if html_body:
            email = EmailMultiAlternatives(
                subject, body, settings.DEFAULT_FROM_EMAIL, [to_email],
            )
            email.attach_alternative(html_body, 'text/html')
            email.send(fail_silently=True)
        else:
            send_mail(subject, body, None, [to_email], fail_silently=True)
    except Exception:
        logger.exception('Failed to send notification email to %s', to_email)
