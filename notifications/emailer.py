import logging

from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_notification_email(to_email, subject, body):
    """Best-effort send — never lets an email failure break the caller (checkout, admin save, etc.)."""
    if not to_email:
        return
    try:
        send_mail(subject, body, None, [to_email], fail_silently=True)
    except Exception:
        logger.exception('Failed to send notification email to %s', to_email)
