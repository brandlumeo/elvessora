import logging
from email.mime.image import MIMEImage

from django.conf import settings
from django.contrib.staticfiles.finders import find as find_static
from django.core.mail import EmailMultiAlternatives, send_mail

logger = logging.getLogger(__name__)

# The brand logo is embedded as an inline (Content-ID) attachment rather than
# linked as a remote image URL — this way it always renders regardless of
# whether a given email client's image proxy successfully fetches an
# external URL. Templates reference it as src="cid:{{ logo_cid }}".
LOGO_STATIC_PATH = 'images/elvessora-logo-horizontal.png'
LOGO_CID = 'elvessora-logo'


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
            # 'related' lets the inline logo travel alongside the HTML
            # alternative instead of showing up as a separate attachment.
            email.mixed_subtype = 'related'

            logo_path = find_static(LOGO_STATIC_PATH)
            if logo_path:
                with open(logo_path, 'rb') as f:
                    logo_image = MIMEImage(f.read())
                logo_image.add_header('Content-ID', f'<{LOGO_CID}>')
                logo_image.add_header('Content-Disposition', 'inline', filename='elvessora-logo.png')
                email.attach(logo_image)
            else:
                logger.warning('Logo static file not found at %s; sending email without it', LOGO_STATIC_PATH)

            email.send(fail_silently=True)
        else:
            send_mail(subject, body, None, [to_email], fail_silently=True)
    except Exception:
        logger.exception('Failed to send notification email to %s', to_email)
