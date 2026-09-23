from django.utils import timezone
from django.utils.html import strip_tags

from notifications.emailer import send_notification_email
from .models import NewsletterSubscriber


def send_campaign(campaign):
    """Sends an EmailCampaign to every active newsletter subscriber and
    marks it sent. Each subscriber gets an individual send (never a single
    email exposing every address in a shared To/Cc list). Returns the
    number of subscribers it was sent to.
    """
    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    plain_text = strip_tags(campaign.body_html)
    for subscriber in subscribers:
        send_notification_email(
            subscriber.email,
            campaign.subject,
            plain_text,
            html_body=campaign.body_html,
        )
    campaign.status = 'sent'
    campaign.sent_at = timezone.now()
    campaign.save(update_fields=['status', 'sent_at'])
    return subscribers.count()
