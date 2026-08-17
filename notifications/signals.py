from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse

from .content import order_content, welcome_content
from .emailer import send_notification_email
from .models import Notification
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


@receiver(post_save, sender=User)
def send_welcome_notification(sender, instance, created, **kwargs):
    if not created:
        return
    title, message, subject, body = welcome_content(instance)
    Notification.objects.create(user=instance, notification_type='welcome', title=title, message=message)
    if instance.email:
        send_notification_email(instance.email, subject, body)


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
        send_notification_email(order.user.email, subject, body)
    elif order.is_guest and order.guest_email:
        send_notification_email(order.guest_email, subject, body)
