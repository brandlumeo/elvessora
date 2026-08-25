import hashlib

from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from .content import login_alert_content, order_content, welcome_content
from .emailer import send_notification_email
from .models import Notification
from .whatsapp import send_whatsapp_message
from accounts.models import KnownLogin
from orders.models import Order

ORDER_STATUS_TYPE_MAP = {
    'confirmed': 'order_confirmed',
    'processing': 'order_processing',
    'shipped': 'order_shipped',
    'out_for_delivery': 'order_out_for_delivery',
    'delivered': 'order_delivered',
    'cancelled': 'order_cancelled',
    'refunded': 'order_refunded',
}


def _dispatch(user, subject, body, whatsapp_message):
    """Send a notification's email/WhatsApp legs per the user's saved channel preferences."""
    profile = getattr(user, 'profile', None)
    if user.email and (not profile or profile.email_notifications):
        send_notification_email(user.email, subject, body)
    if profile and profile.whatsapp_notifications and profile.phone:
        send_whatsapp_message(profile.phone, whatsapp_message)


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    if not created:
        return
    title, message, subject, body = welcome_content(instance)
    Notification.objects.create(user=instance, notification_type='welcome', title=title, message=message)
    _dispatch(instance, subject, body, message)


@receiver(pre_save, sender=Order)
def stash_old_order_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_status = None
        return
    instance._old_status = Order.objects.filter(pk=instance.pk).values_list('status', flat=True).first()


@receiver(post_save, sender=Order)
def notify_order_event(sender, instance, created, **kwargs):
    order = instance

    if created:
        notification_type = 'order_placed'
    else:
        old_status = getattr(order, '_old_status', None)
        if old_status is None or old_status == order.status:
            return
        notification_type = ORDER_STATUS_TYPE_MAP.get(order.status)
        if not notification_type:
            return

    title, message, subject, body = order_content(notification_type, order)

    if order.user_id:
        link = reverse('orders:order_detail', args=[order.order_number])
        Notification.objects.create(
            user=order.user,
            notification_type=notification_type,
            title=title,
            message=message,
            link=link,
            order=order,
        )
        _dispatch(order.user, subject, body, message)
    elif order.is_guest and order.guest_email:
        send_notification_email(order.guest_email, subject, body)


def _client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def _describe_device(user_agent):
    ua = (user_agent or '').lower()
    if 'edg/' in ua:
        browser = 'Edge'
    elif 'chrome' in ua and 'chromium' not in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua and 'chrome' not in ua:
        browser = 'Safari'
    else:
        browser = 'a browser'

    if 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    elif 'windows' in ua:
        os_name = 'Windows'
    elif 'mac os' in ua:
        os_name = 'Mac'
    elif 'linux' in ua:
        os_name = 'Linux'
    else:
        os_name = 'an unknown device'

    return f'{browser} on {os_name}'


@receiver(user_logged_in)
def alert_new_login(sender, request, user, **kwargs):
    """Send a security alert the first time we see a given device/IP for this
    user — repeat logins from an already-seen device stay silent."""
    ip = _client_ip(request)
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    fingerprint = hashlib.sha256(f'{ip}|{user_agent}'.encode()).hexdigest()

    known, created = KnownLogin.objects.get_or_create(
        user=user,
        fingerprint=fingerprint,
        defaults={'ip_address': ip or None, 'user_agent': user_agent},
    )
    if not created:
        known.save()  # bumps last_seen via auto_now
        return

    device = _describe_device(user_agent)
    title, message, subject, body = login_alert_content(user, ip, device, timezone.now())
    Notification.objects.create(user=user, notification_type='login_alert', title=title, message=message)
    _dispatch(user, subject, body, message)
