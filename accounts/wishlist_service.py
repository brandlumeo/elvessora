from .models import Wishlist


def ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def wishlist_queryset(request):
    if request.user.is_authenticated:
        return Wishlist.objects.filter(user=request.user).select_related('product')
    session_key = ensure_session_key(request)
    return Wishlist.objects.filter(
        user__isnull=True, session_key=session_key
    ).select_related('product')


def wishlist_product_ids(request):
    return list(wishlist_queryset(request).values_list('product_id', flat=True))


def toggle_wishlist(request, product):
    """Add or remove product. Returns (added: bool)."""
    if request.user.is_authenticated:
        item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if not created:
            item.delete()
            return False
        return True

    session_key = ensure_session_key(request)
    item, created = Wishlist.objects.get_or_create(
        user=None,
        session_key=session_key,
        product=product,
    )
    if not created:
        item.delete()
        return False
    return True


def merge_session_wishlist(request, user):
    """Move guest wishlist items onto the user after login/register."""
    session_key = request.session.session_key
    if not session_key or not user or not user.is_authenticated:
        return
    guest_items = Wishlist.objects.filter(user__isnull=True, session_key=session_key)
    for item in guest_items:
        Wishlist.objects.get_or_create(user=user, product=item.product)
        item.delete()
