from django.conf import settings

from core.models import SiteSettings
from marketing.models import PromoPopup
from products.models import FragranceFamily, Occasion


def site_context(request):
    settings_obj = SiteSettings.get()
    popup = PromoPopup.objects.filter(is_active=True).first()
    unread_notifications_count = 0
    if request.user.is_authenticated:
        unread_notifications_count = request.user.notifications.filter(is_read=False).count()
    return {
        'site_settings': settings_obj,
        'promo_popup': popup,
        'nav_families': FragranceFamily.objects.all()[:10],
        'nav_occasions': Occasion.objects.all()[:10],
        'google_client_id': getattr(settings, 'GOOGLE_CLIENT_ID', ''),
        'unread_notifications_count': unread_notifications_count,
    }
