import json
import logging
import secrets
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.core.cache import cache
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy, reverse
from django.views.decorators.http import require_POST
from .forms import RegisterForm, LoginForm, ProfileForm, AddressForm, ElvessoraPasswordResetForm
from .models import Address, UserProfile
from .wishlist_service import merge_session_wishlist, toggle_wishlist, wishlist_queryset
from products.models import Product
from core.flash import notify_product_action

logger = logging.getLogger(__name__)
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://www.googleapis.com/oauth2/v3/userinfo'


def _unique_username(base):
    base = (base or 'user')[:30]
    candidate = base
    n = 1
    while User.objects.filter(username=candidate).exists():
        suffix = str(n)
        candidate = f'{base[: 30 - len(suffix)]}{suffix}'
        n += 1
    return candidate


def _user_from_google_profile(sub, email, given_name='', family_name=''):
    profile = UserProfile.objects.filter(google_sub=sub).select_related('user').first()
    if profile:
        return profile.user

    email = (email or '').strip().lower()
    if not email:
        raise ValueError('Google account email is required.')

    user = User.objects.filter(email__iexact=email).first()
    if user:
        user.profile.google_sub = sub
        if given_name and not user.first_name:
            user.first_name = given_name[:150]
        if family_name and not user.last_name:
            user.last_name = family_name[:150]
        user.save()
        user.profile.save()
        return user

    username = _unique_username(email.split('@')[0])
    user = User(
        username=username,
        email=email,
        first_name=(given_name or '')[:150],
        last_name=(family_name or '')[:150],
    )
    user.set_unusable_password()
    user.save()
    user.profile.google_sub = sub
    user.profile.save()
    return user


def _google_redirect_uri(request):
    configured = getattr(settings, 'GOOGLE_REDIRECT_URI', '').strip()
    if configured:
        return configured
    return request.build_absolute_uri(reverse('accounts:google_callback'))


def _safe_next_url(candidate):
    if candidate and candidate.startswith('/') and not candidate.startswith('//'):
        return candidate
    return reverse('core:home')


def _client_ip(request):
    return request.META.get('REMOTE_ADDR', 'unknown')


def _rate_limited(key, limit, window_seconds):
    """Lightweight cache-based throttle: True once `limit` hits land within `window_seconds`."""
    count = cache.get(key, 0)
    if count >= limit:
        return True
    cache.set(key, count + 1, window_seconds)
    return False


def _exchange_google_code(code, redirect_uri):
    """Exchange auth code for tokens. Returns (token_data, error_message)."""
    token_payload = urllib.parse.urlencode({
        'code': code,
        'client_id': settings.GOOGLE_CLIENT_ID.strip(),
        'client_secret': settings.GOOGLE_CLIENT_SECRET.strip(),
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
    }).encode('utf-8')

    token_req = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=token_payload,
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )
    try:
        with urllib.request.urlopen(token_req, timeout=15) as resp:
            return json.loads(resp.read().decode('utf-8')), None
    except urllib.error.HTTPError as exc:
        body = ''
        try:
            body = exc.read().decode('utf-8', errors='replace')
            payload = json.loads(body)
        except (json.JSONDecodeError, ValueError, UnicodeError):
            payload = {}
        err = payload.get('error') or f'http_{exc.code}'
        desc = payload.get('error_description') or body[:200] or str(exc)
        return None, f'{err}: {desc}'
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as exc:
        return None, str(exc)


def google_start(request):
    """Begin Google OAuth (full-page redirect — more reliable than popup)."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(
            request,
            'Google Sign-In is not fully configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.',
        )
        return redirect('accounts:login')

    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    request.session['google_oauth_next'] = _safe_next_url(
        request.GET.get('next') or request.POST.get('next')
    )
    # Persist redirect URI used at start so callback exchange matches exactly
    redirect_uri = _google_redirect_uri(request)
    request.session['google_oauth_redirect_uri'] = redirect_uri

    params = {
        'client_id': settings.GOOGLE_CLIENT_ID.strip(),
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }
    return redirect(f'{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}')


def google_callback(request):
    """Handle Google OAuth redirect and log the user in."""
    if _rate_limited(f'google-callback:{_client_ip(request)}', limit=20, window_seconds=300):
        messages.error(request, 'Too many sign-in attempts. Please try again shortly.')
        return redirect('accounts:login')

    if request.GET.get('error'):
        messages.error(request, 'Google Sign-In was cancelled or denied.')
        return redirect('accounts:login')

    state = request.GET.get('state', '')
    expected = request.session.pop('google_oauth_state', '')
    next_url = _safe_next_url(request.session.pop('google_oauth_next', None))
    redirect_uri = request.session.pop('google_oauth_redirect_uri', None) or _google_redirect_uri(request)

    if not state or not expected or state != expected:
        messages.error(request, 'Google Sign-In failed (invalid state). Please try again.')
        return redirect('accounts:login')

    code = request.GET.get('code', '').strip()
    if not code:
        messages.error(request, 'Google Sign-In failed (missing code). Please try again.')
        return redirect('accounts:login')

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Google Sign-In is not configured on the server.')
        return redirect('accounts:login')

    token_data, exchange_error = _exchange_google_code(code, redirect_uri)
    if exchange_error:
        logger.warning('Google token exchange failed: %s', exchange_error)
        hint = exchange_error
        lower = exchange_error.lower()
        if 'invalid_client' in lower:
            hint = (
                'Invalid Google Client Secret. Reset the secret in Google Console '
                'and paste the exact new value into .env as GOOGLE_CLIENT_SECRET, then restart the server.'
            )
        elif 'redirect_uri' in lower:
            hint = (
                f'Redirect URI mismatch. In Google Console add exactly: {redirect_uri}'
            )
        messages.error(request, f'Could not complete Google Sign-In ({hint})')
        return redirect('accounts:login')

    access_token = token_data.get('access_token')
    if not access_token:
        messages.error(request, 'Could not complete Google Sign-In (no access token).')
        return redirect('accounts:login')

    try:
        info_req = urllib.request.Request(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
        )
        with urllib.request.urlopen(info_req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        messages.error(request, 'Could not verify Google account details.')
        return redirect('accounts:login')

    sub = data.get('sub')
    email = data.get('email')
    if not sub or not email:
        messages.error(request, 'Google account did not return a verified email.')
        return redirect('accounts:login')
    if data.get('email_verified') is False:
        messages.error(request, 'Google email is not verified.')
        return redirect('accounts:login')

    try:
        user = _user_from_google_profile(
            sub=sub,
            email=email,
            given_name=data.get('given_name', ''),
            family_name=data.get('family_name', ''),
        )
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect('accounts:login')

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    merge_session_wishlist(request, user)
    messages.success(request, 'Welcome! Signed in with Google.')
    return redirect(next_url)


def register(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        merge_session_wishlist(request, user)
        messages.success(request, 'Welcome to Elvessora! Your account has been created.')
        return redirect('core:home')
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('core:home')
    if request.method == 'POST' and _rate_limited(f'login-attempts:{_client_ip(request)}', limit=10, window_seconds=300):
        messages.error(request, 'Too many login attempts. Please try again in a few minutes.')
        form = LoginForm(request, next_url=request.GET.get('next', ''))
        return render(request, 'accounts/login.html', {'form': form})
    form = LoginForm(request, data=request.POST or None, next_url=request.GET.get('next', ''))
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        merge_session_wishlist(request, user)
        messages.success(request, 'Welcome back!')
        next_url = _safe_next_url(request.GET.get('next') or request.POST.get('next'))
        return redirect(next_url)
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user.profile, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def addresses(request):
    user_addresses = request.user.addresses.all()
    form = AddressForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user
        address.save()
        messages.success(request, 'Address saved.')
        return redirect('accounts:addresses')
    return render(request, 'accounts/addresses.html', {
        'addresses': user_addresses,
        'form': form,
    })


@login_required
@require_POST
def address_delete(request, pk):
    Address.objects.filter(pk=pk, user=request.user).delete()
    messages.success(request, 'Address removed.')
    return redirect('accounts:addresses')


def wishlist(request):
    items = wishlist_queryset(request)
    return render(request, 'accounts/wishlist.html', {'items': items})


@require_POST
def wishlist_toggle(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    added = toggle_wishlist(request, product)
    if added:
        request.session['open_drawer'] = 'wishlist'
        notify_product_action(
            request,
            product_name=product.name,
            action='added to wishlist',
            product_url=product.get_absolute_url(),
            secondary_label='View wishlist',
            secondary_url=reverse('accounts:wishlist'),
        )
    else:
        notify_product_action(
            request,
            product_name=product.name,
            action='removed from wishlist',
            product_url=product.get_absolute_url(),
            secondary_label='View wishlist',
            secondary_url=reverse('accounts:wishlist'),
        )
        if request.GET.get('drawer') == '1':
            request.session['open_drawer'] = 'wishlist'

    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('accounts:wishlist')


@login_required
def order_history(request):
    orders = request.user.orders.all()
    return render(request, 'accounts/order_history.html', {'orders': orders})


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html'
    subject_template_name = 'accounts/password_reset_subject.txt'
    form_class = ElvessoraPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')

    def post(self, request, *args, **kwargs):
        if _rate_limited(f'pwreset-attempts:{_client_ip(request)}', limit=5, window_seconds=3600):
            # Redirect to the same "done" page regardless — don't reveal whether the throttle
            # or a real send is why no new email arrives (matches Django's no-enumeration design).
            return redirect(self.success_url)
        return super().post(request, *args, **kwargs)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'
