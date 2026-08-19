from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from products.models import Product, ProductVariant, GiftSet
from core.flash import notify_product_action
from .cart_service import CartService


def cart_detail(request):
    cart_service = CartService(request)
    coupon_code = request.session.get('coupon_code', '')
    coupon = cart_service.apply_coupon(coupon_code) if coupon_code else None
    totals = cart_service.calculate_totals(coupon)
    return render(request, 'cart/cart.html', {
        'cart_items': cart_service.cart.items.all(),
        'totals': totals,
        'coupon': coupon,
        'coupon_code': coupon_code,
    })


def add_to_cart(request):
    if request.method != 'POST':
        return redirect('products:shop')

    cart_service = CartService(request)
    product_id = request.POST.get('product_id')
    variant_id = request.POST.get('variant_id')
    gift_set_id = request.POST.get('gift_set_id')
    try:
        quantity = max(1, int(request.POST.get('quantity', 1)))
    except (TypeError, ValueError):
        quantity = 1
    gift_wrapping = request.POST.get('gift_wrapping') == 'on'
    gift_message = request.POST.get('gift_message', '')

    if gift_set_id:
        gift_set = get_object_or_404(GiftSet, id=gift_set_id, is_active=True)
        try:
            cart_service.add_gift_set(gift_set, quantity, gift_wrapping, gift_message)
            request.session['open_drawer'] = 'cart'
            notify_product_action(
                request,
                product_name=gift_set.name,
                action='added to cart',
                product_url=gift_set.get_absolute_url(),
                secondary_label='View cart',
                secondary_url=reverse('cart:cart'),
            )
        except ValueError as exc:
            messages.error(request, str(exc))
    else:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        variant = None
        if variant_id:
            variant = get_object_or_404(ProductVariant, id=variant_id, product=product)
        try:
            cart_service.add_product(product, variant, quantity, gift_wrapping, gift_message)
            request.session['open_drawer'] = 'cart'
            notify_product_action(
                request,
                product_name=product.name,
                action='added to cart',
                product_url=product.get_absolute_url(),
                secondary_label='View cart',
                secondary_url=reverse('cart:cart'),
            )
        except ValueError as exc:
            messages.error(request, str(exc))

    if request.POST.get('buy_now'):
        return redirect('orders:checkout')
    return redirect(request.META.get('HTTP_REFERER', 'cart:cart'))


def update_cart(request, item_id):
    if request.method == 'POST':
        try:
            quantity = max(0, int(request.POST.get('quantity', 1)))
        except (TypeError, ValueError):
            messages.error(request, 'Invalid quantity.')
            return redirect('cart:cart')
        try:
            CartService(request).update_quantity(item_id, quantity)
            messages.success(request, 'Cart updated.')
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect('cart:cart')


def remove_from_cart(request, item_id):
    if request.method != 'POST':
        return redirect('cart:cart')
    CartService(request).remove_item(item_id)
    messages.info(request, 'Item removed from cart.')
    next_target = request.POST.get('next') or request.GET.get('next')
    if next_target == 'drawer':
        request.session['open_drawer'] = 'cart'
        return redirect(request.META.get('HTTP_REFERER') or reverse('core:home'))
    return redirect('cart:cart')


def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip()
        cart_service = CartService(request)
        coupon = cart_service.apply_coupon(code)
        if coupon:
            request.session['coupon_code'] = code
            messages.success(request, f'Coupon "{code}" applied!')
        else:
            request.session.pop('coupon_code', None)
            messages.error(request, 'Invalid or expired coupon code.')
    return redirect('cart:cart')
