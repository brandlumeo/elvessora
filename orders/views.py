from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import razorpay
import hmac
import hashlib
import json

from cart.cart_service import CartService
from core.models import SiteSettings
from . import tamara
from .forms import CheckoutForm
from .models import Order, OrderItem, Coupon, Payment

ORDER_ACCESS_SESSION_KEY = 'order_access'


def _grant_order_access(request, order_number):
    """Remember, in this browser session, that this visitor just created this order."""
    granted = request.session.get(ORDER_ACCESS_SESSION_KEY, [])
    granted.append(order_number)
    request.session[ORDER_ACCESS_SESSION_KEY] = granted[-20:]


def _can_view_order(request, order):
    if request.user.is_authenticated and order.user_id == request.user.id:
        return True
    return order.order_number in request.session.get(ORDER_ACCESS_SESSION_KEY, [])


def _decrement_stock(order):
    for item in order.items.all():
        if item.variant:
            item.variant.stock_quantity = max(0, item.variant.stock_quantity - item.quantity)
            item.variant.save()


def checkout(request):
    cart_service = CartService(request)
    cart = cart_service.cart
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:shop')

    out_of_stock_items = [
        item for item in cart.items.select_related('variant')
        if item.variant and item.quantity > item.variant.stock_quantity
    ]
    if out_of_stock_items:
        names = ', '.join(f'{item.product.name} ({item.variant.size})' for item in out_of_stock_items)
        messages.error(request, f'Not enough stock for: {names}. Please update your cart.')
        return redirect('cart:cart')

    coupon_code = request.session.get('coupon_code', '')
    coupon = cart_service.apply_coupon(coupon_code) if coupon_code else None
    totals = cart_service.calculate_totals(coupon)

    initial = {}
    if request.user.is_authenticated:
        default_address = request.user.addresses.filter(is_default=True).first()
        if default_address:
            initial = {
                'shipping_name': default_address.full_name,
                'shipping_phone': default_address.phone,
                'shipping_address': f'{default_address.address_line1}\n{default_address.address_line2}'.strip(),
                'shipping_city': default_address.city,
                'shipping_state': default_address.state,
                'shipping_pincode': default_address.pincode,
                'shipping_country': default_address.country,
            }

    form = CheckoutForm(request.POST or None, initial=initial, user=request.user)

    if request.method == 'POST' and form.is_valid():
        if not request.user.is_authenticated and not form.cleaned_data.get('guest_email'):
            messages.error(request, 'Email is required for guest checkout.')
            return render(request, 'orders/checkout.html', {'form': form, 'totals': totals, 'cart_items': cart.items.all()})

        payment_method = form.cleaned_data['payment_method']
        razorpay_configured = bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)
        online_configured = {'razorpay': razorpay_configured, 'tamara': tamara.is_configured()}.get(payment_method, True)
        if payment_method != 'cod' and not online_configured and not settings.DEBUG:
            messages.error(request, 'That payment method is currently unavailable. Please choose another.')
            return render(request, 'orders/checkout.html', {'form': form, 'totals': totals, 'cart_items': cart.items.all()})

        post_coupon = cart_service.apply_coupon(form.cleaned_data.get('coupon_code', ''))
        if post_coupon:
            coupon = post_coupon
            totals = cart_service.calculate_totals(coupon)

        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            is_guest=not request.user.is_authenticated,
            guest_email=form.cleaned_data.get('guest_email', '') or (request.user.email if request.user.is_authenticated else ''),
            shipping_name=form.cleaned_data['shipping_name'],
            shipping_phone=form.cleaned_data['shipping_phone'],
            shipping_address=form.cleaned_data['shipping_address'],
            shipping_city=form.cleaned_data['shipping_city'],
            shipping_state=form.cleaned_data['shipping_state'],
            shipping_pincode=form.cleaned_data['shipping_pincode'],
            shipping_country=form.cleaned_data['shipping_country'],
            subtotal=totals['subtotal'],
            shipping_charge=totals['shipping'],
            tax_amount=totals['tax'],
            discount_amount=totals['discount'],
            total=totals['total'],
            coupon=coupon,
            coupon_code=coupon.code if coupon else '',
            payment_method=payment_method,
            notes=form.cleaned_data.get('notes', ''),
            estimated_delivery=SiteSettings.get().estimated_delivery_days,
            courier_name=SiteSettings.get().courier_partner,
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                gift_set=item.gift_set,
                product_name=item.gift_set.name if item.gift_set else item.product.name,
                variant_size=item.variant.size if item.variant else '',
                quantity=item.quantity,
                unit_price=item.unit_price,
                gift_message=item.gift_message,
                gift_wrapping=item.gift_wrapping,
            )

        if coupon:
            coupon.used_count += 1
            coupon.save()

        request.session.pop('coupon_code', None)
        _grant_order_access(request, order.order_number)

        if payment_method == 'cod':
            _decrement_stock(order)
            order.payment_status = 'pending'
            order.status = 'confirmed'
            order.save()
            cart_service.clear()
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('orders:order_confirmation', order_number=order.order_number)

        if payment_method == 'razorpay' and razorpay_configured:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                'amount': int(order.total * 100),
                'currency': 'AED',
                'receipt': order.order_number,
            })
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            Payment.objects.create(
                order=order,
                razorpay_order_id=razorpay_order['id'],
                amount=order.total,
            )
            # Stock is decremented in payment_verify() once the signature is confirmed,
            # so an abandoned/failed online payment never permanently reduces stock.
            return render(request, 'orders/payment.html', {
                'order': order,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': int(order.total * 100),
            })

        if payment_method == 'tamara' and tamara.is_configured():
            try:
                session = tamara.create_checkout_session(
                    order,
                    success_url=request.build_absolute_uri(reverse('orders:tamara_success')),
                    failure_url=request.build_absolute_uri(reverse('orders:tamara_failure')),
                    cancel_url=request.build_absolute_uri(reverse('orders:tamara_cancel')),
                )
            except tamara.TamaraError:
                order.delete()
                messages.error(request, "We couldn't start your Tamara checkout. Please try another payment method.")
                return redirect('orders:checkout')

            order.tamara_checkout_id = session['checkout_id']
            order.tamara_order_id = session['order_id']
            order.save()
            # Stock is decremented in tamara_success() once the payment is captured,
            # so an abandoned/failed Tamara checkout never permanently reduces stock.
            return redirect(session['checkout_url'])

        # DEBUG-only fallback: no online payment provider configured, but this is a
        # dev/demo environment (see README) — auto-confirm so the flow is testable end-to-end.
        _decrement_stock(order)
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        cart_service.clear()
        messages.success(request, f'Order {order.order_number} placed successfully!')
        return redirect('orders:order_confirmation', order_number=order.order_number)

    return render(request, 'orders/checkout.html', {
        'form': form,
        'totals': totals,
        'cart_items': cart.items.all(),
    })


@csrf_exempt
def payment_verify(request):
    if request.method == 'POST':
        payment_id = request.POST.get('razorpay_payment_id')
        order_id = request.POST.get('razorpay_order_id')
        signature = request.POST.get('razorpay_signature')

        if not order_id or not payment_id:
            messages.error(request, 'Invalid payment verification request.')
            return redirect('cart:cart')

        order = Order.objects.filter(razorpay_order_id=order_id).order_by('-id').first()
        if order is None:
            messages.error(request, 'Order not found.')
            return redirect('cart:cart')

        generated = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f'{order_id}|{payment_id}'.encode(),
            hashlib.sha256,
        ).hexdigest()

        if hmac.compare_digest(generated, signature or ''):
            already_paid = order.payment_status == 'paid'
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.razorpay_payment_id = payment_id
            order.save()
            if not already_paid:
                _decrement_stock(order)
            payment = order.payment
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.status = 'paid'
            payment.save()
            _grant_order_access(request, order.order_number)
            CartService(request).clear()
            return redirect('orders:order_confirmation', order_number=order.order_number)

        order.payment_status = 'failed'
        order.save()
        _grant_order_access(request, order.order_number)
        messages.error(request, 'Payment verification failed.')
        return redirect('orders:payment_failed', order_number=order.order_number)

    return redirect('cart:cart')


def _find_tamara_order(request):
    tamara_order_id = request.GET.get('order_id') or request.GET.get('orderId')
    order = None
    if tamara_order_id:
        order = Order.objects.filter(tamara_order_id=tamara_order_id).order_by('-id').first()
    if order is None:
        # Fallback: the most recent Tamara order this browser session created,
        # in case Tamara's redirect doesn't carry the order_id query param.
        granted = request.session.get(ORDER_ACCESS_SESSION_KEY, [])
        order = Order.objects.filter(
            order_number__in=granted, payment_method='tamara',
        ).order_by('-id').first()
    return order


def tamara_success(request):
    order = _find_tamara_order(request)
    if order is None:
        messages.error(request, 'Order not found.')
        return redirect('cart:cart')

    if order.payment_status == 'paid':
        return redirect('orders:order_confirmation', order_number=order.order_number)

    try:
        tamara_order = tamara.get_order(order.tamara_order_id)
        if tamara_order.get('status') == 'approved':
            tamara.authorise_order(order.tamara_order_id)
        tamara.capture_order(order.tamara_order_id, order.total)
    except tamara.TamaraError:
        order.payment_status = 'failed'
        order.save()
        _grant_order_access(request, order.order_number)
        messages.error(request, "We couldn't confirm your Tamara payment. Please contact support.")
        return redirect('orders:payment_failed', order_number=order.order_number)

    order.payment_status = 'paid'
    order.status = 'confirmed'
    order.save()
    _decrement_stock(order)
    _grant_order_access(request, order.order_number)
    CartService(request).clear()
    return redirect('orders:order_confirmation', order_number=order.order_number)


def tamara_failure(request):
    order = _find_tamara_order(request)
    if order is not None:
        order.payment_status = 'failed'
        order.save()
        _grant_order_access(request, order.order_number)
        messages.error(request, 'Your Tamara payment was declined. Please try another payment method.')
        return redirect('orders:payment_failed', order_number=order.order_number)
    messages.error(request, 'Your Tamara payment was declined.')
    return redirect('cart:cart')


def tamara_cancel(request):
    order = _find_tamara_order(request)
    if order is not None:
        order.delete()
    messages.info(request, 'Checkout cancelled. Your cart is still saved.')
    return redirect('cart:cart')


@csrf_exempt
def tamara_webhook(request):
    """Safety-net webhook: keeps order status correct even if the shopper
    closes the tab before the success/failure redirect completes.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    token = request.GET.get('tamaraToken') or request.META.get('HTTP_AUTHORIZATION', '').replace('Bearer ', '')
    payload = tamara.verify_notification_token(token)
    if payload is None:
        return HttpResponse(status=401)

    try:
        body = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)

    tamara_order_id = body.get('order_id')
    event_type = body.get('event_type')
    order = Order.objects.filter(tamara_order_id=tamara_order_id).order_by('-id').first()
    if order is None:
        return HttpResponse(status=404)

    if event_type in ('order_captured', 'order_approved', 'order_authorised'):
        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.save()
            _decrement_stock(order)
    elif event_type in ('order_declined', 'order_expired'):
        order.payment_status = 'failed'
        order.save()
    elif event_type == 'order_canceled':
        order.payment_status = 'failed'
        order.status = 'cancelled'
        order.save()
    elif event_type == 'order_refunded':
        order.payment_status = 'refunded'
        order.status = 'refunded'
        order.save()

    return HttpResponse(status=200)


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not _can_view_order(request, order):
        messages.error(request, "We couldn't verify access to that order. Use order tracking with your email instead.")
        return redirect('orders:tracking')
    return render(request, 'orders/confirmation.html', {'order': order})


def payment_failed(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if not _can_view_order(request, order):
        messages.error(request, "We couldn't verify access to that order. Use order tracking with your email instead.")
        return redirect('orders:tracking')
    return render(request, 'orders/payment_failed.html', {'order': order})


def order_tracking(request):
    order_number = request.GET.get('order_number', '').strip()
    email = request.GET.get('email', '').strip()
    order = None
    if order_number and email:
        order = Order.objects.filter(order_number=order_number).filter(
            Q(guest_email__iexact=email) | Q(user__email__iexact=email)
        ).first()
        if order is None:
            messages.error(request, 'No order found for that order number and email.')
    elif order_number and not email:
        messages.error(request, 'Please enter the email used for this order.')
    return render(request, 'orders/tracking.html', {'order': order, 'order_number': order_number})


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})


@login_required
def reorder(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    cart_service = CartService(request)
    for item in order.items.all():
        if item.gift_set:
            cart_service.add_gift_set(item.gift_set, item.quantity)
        elif item.product:
            cart_service.add_product(item.product, item.variant, item.quantity)
    messages.success(request, 'Items added to cart for reorder.')
    return redirect('cart:cart')
