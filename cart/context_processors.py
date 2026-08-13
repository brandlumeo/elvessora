from .cart_service import CartService
from accounts.wishlist_service import wishlist_queryset


def cart_context(request):
    cart_service = CartService(request)
    cart = cart_service.cart
    cart_items = list(
        cart.items.select_related('product', 'variant', 'gift_set').all()
    )
    wishlist_items = list(
        wishlist_queryset(request)
        .select_related('product')
        .prefetch_related('product__variants', 'product__images')[:20]
    )
    wishlist_ids = [item.product_id for item in wishlist_items]

    open_drawer = ''
    if hasattr(request, 'session'):
        open_drawer = request.session.pop('open_drawer', '') or ''

    return {
        'cart': cart,
        'cart_items': cart_items,
        'cart_count': cart.item_count,
        'cart_subtotal': cart.subtotal,
        'wishlist_count': len(wishlist_ids),
        'wishlist_product_ids': wishlist_ids,
        'wishlist_items': wishlist_items,
        'open_drawer': open_drawer,
    }
