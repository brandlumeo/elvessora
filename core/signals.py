from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver


def _client_ip(request):
    if not request:
        return None
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    from .models import LoginHistory, ActivityLog
    LoginHistory.objects.create(
        user=user,
        ip_address=_client_ip(request),
        user_agent=(request.META.get('HTTP_USER_AGENT', '')[:300] if request else ''),
        success=True,
    )
    ActivityLog.objects.create(
        user=user,
        action='login',
        object_repr=user.get_username(),
        ip_address=_client_ip(request),
    )


@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    from django.contrib.auth.models import User
    from .models import LoginHistory, ActivityLog
    username = (credentials or {}).get('username') or ''
    user = User.objects.filter(username=username).first()
    if user:
        LoginHistory.objects.create(
            user=user,
            ip_address=_client_ip(request),
            user_agent=(request.META.get('HTTP_USER_AGENT', '')[:300] if request else ''),
            success=False,
        )
    ActivityLog.objects.create(
        user=user,
        action='login_failed',
        object_repr=username,
        ip_address=_client_ip(request),
    )
