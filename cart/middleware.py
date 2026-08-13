from django.utils.deprecation import MiddlewareMixin
from .cart_service import CartService
from accounts.wishlist_service import merge_session_wishlist


class MergeCartMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated and request.session.session_key:
            CartService(request).merge_session_cart(request.user)
            merge_session_wishlist(request, request.user)
