from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import json
import logging
import time

from cart.cart_service import CartService
from core.models import SiteSettings
from . import nomod, tamara, tabby, tap
from .forms import CheckoutForm
from .models import Order, OrderItem, Coupon, Payment

logger = logging.getLogger(__name__)

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

    form = CheckoutForm(
        request.POST or None, initial=initial, user=request.user,
        online_available=nomod.is_configured() or settings.DEBUG,
    )

    if request.method == 'POST' and form.is_valid():
        if not request.user.is_authenticated and not form.cleaned_data.get('guest_email'):
            messages.error(request, 'Email is required for guest checkout.')
            return render(request, 'orders/checkout.html', {'form': form, 'totals': totals, 'cart_items': cart.items.all()})

        payment_method = form.cleaned_data['payment_method']
        online_configured = {
            'tamara': tamara.is_configured(), 'tabby': tabby.is_configured(), 'tap': tap.is_configured(),
            'nomod': nomod.is_configured(),
        }.get(payment_method, True)
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

        if payment_method == 'tabby' and tabby.is_configured():
            try:
                session = tabby.create_checkout_session(
                    order,
                    success_url=request.build_absolute_uri(reverse('orders:tabby_success')),
                    failure_url=request.build_absolute_uri(reverse('orders:tabby_failure')),
                    cancel_url=request.build_absolute_uri(reverse('orders:tabby_cancel')),
                )
            except tabby.TabbyError:
                order.delete()
                messages.error(request, "We couldn't start your Tabby checkout. Please try another payment method.")
                return redirect('orders:checkout')

            order.tabby_payment_id = session['payment_id']
            order.save()
            return redirect(session['checkout_url'])

        if payment_method == 'tap' and tap.is_configured():
            try:
                charge = tap.create_charge(
                    order,
                    redirect_url=request.build_absolute_uri(reverse('orders:tap_return')),
                    webhook_url=request.build_absolute_uri(reverse('orders:tap_webhook')),
                )
            except tap.TapError:
                order.delete()
                messages.error(request, "We couldn't start your card payment. Please try another payment method.")
                return redirect('orders:checkout')

            order.tap_charge_id = charge['charge_id']
            order.save()
            # Stock is decremented in tap_return() once the charge is confirmed
            # CAPTURED, so an abandoned/failed Tap charge never permanently
            # reduces stock.
            return redirect(charge['checkout_url'])

        if payment_method == 'nomod' and nomod.is_configured():
            # Re-read the stored (DB-rounded) totals so the amount sent to
            # Nomod is exactly the amount we verify against on return.
            order.refresh_from_db()

            def nomod_url(name):
                return f"{request.build_absolute_uri(reverse(name))}?order={order.order_number}"

            try:
                nomod_session = nomod.create_checkout(
                    order,
                    success_url=nomod_url('orders:nomod_success'),
                    failure_url=nomod_url('orders:nomod_failure'),
                    cancelled_url=nomod_url('orders:nomod_cancel'),
                )
            except nomod.NomodError:
                order.delete()
                messages.error(request, "We couldn't start your online payment. Please try again or choose Cash on Delivery.")
                return redirect('orders:checkout')

            order.nomod_checkout_id = nomod_session['checkout_id']
            order.save(update_fields=['nomod_checkout_id', 'updated_at'])
            # Stock is decremented only once Nomod confirms the checkout is
            # paid (return handler, webhook or reconcile command), so an
            # abandoned checkout never permanently reduces stock.
            return redirect(nomod_session['checkout_url'])

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
def invoice_download(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if order.payment_status != 'paid':
        messages.error(request, 'An invoice is only available for paid orders.')
        return redirect('orders:order_detail', order_number=order.order_number)

    from .invoicing import render_invoice_pdf
    pdf_bytes = render_invoice_pdf(order)
    if pdf_bytes is None:
        messages.error(request, "We couldn't generate your invoice right now. Please try again shortly.")
        return redirect('orders:order_detail', order_number=order.order_number)

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice-{order.order_number}.pdf"'
    return response


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


def _find_tabby_order(request):
    tabby_payment_id = request.GET.get('payment_id')
    order = None
    if tabby_payment_id:
        order = Order.objects.filter(tabby_payment_id=tabby_payment_id).order_by('-id').first()
    if order is None:
        granted = request.session.get(ORDER_ACCESS_SESSION_KEY, [])
        order = Order.objects.filter(
            order_number__in=granted, payment_method='tabby',
        ).order_by('-id').first()
    return order


def tabby_success(request):
    order = _find_tabby_order(request)
    if order is None:
        messages.error(request, 'Order not found.')
        return redirect('cart:cart')

    if order.payment_status == 'paid':
        return redirect('orders:order_confirmation', order_number=order.order_number)

    try:
        payment = tabby.get_payment(order.tabby_payment_id)
        if payment.get('status') == 'AUTHORIZED':
            tabby.capture_payment(order.tabby_payment_id, order.total)
        elif payment.get('status') == 'CLOSED':
            pass
        else:
            raise tabby.TabbyError(f"Payment status is {payment.get('status')}, expected AUTHORIZED or CLOSED")
    except tabby.TabbyError as e:
        order.payment_status = 'failed'
        order.save()
        _grant_order_access(request, order.order_number)
        messages.error(request, "We couldn't confirm your Tabby payment. Please contact support.")
        return redirect('orders:payment_failed', order_number=order.order_number)

    order.payment_status = 'paid'
    order.status = 'confirmed'
    order.save()
    _decrement_stock(order)
    _grant_order_access(request, order.order_number)
    CartService(request).clear()
    return redirect('orders:order_confirmation', order_number=order.order_number)


def tabby_failure(request):
    order = _find_tabby_order(request)
    if order is not None:
        order.payment_status = 'failed'
        order.save()
        _grant_order_access(request, order.order_number)
        messages.error(request, 'Your Tabby payment was declined. Please try another payment method.')
        return redirect('orders:payment_failed', order_number=order.order_number)
    messages.error(request, 'Your Tabby payment was declined.')
    return redirect('cart:cart')


def tabby_cancel(request):
    order = _find_tabby_order(request)
    if order is not None:
        order.delete()
    messages.info(request, 'Checkout cancelled. Your cart is still saved.')
    return redirect('cart:cart')


@csrf_exempt
def tabby_webhook(request):
    """Fallback webhook for Tabby if the user drops off before redirecting."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        body = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)

    payment_id = body.get('id')
    order = Order.objects.filter(tabby_payment_id=payment_id).order_by('-id').first()
    if order is None:
        return HttpResponse(status=404)

    # This endpoint is unauthenticated, so never trust the posted status:
    # re-fetch the payment from Tabby and act on what Tabby itself reports.
    try:
        status = tabby.get_payment(payment_id).get('status')
    except tabby.TabbyError:
        return HttpResponse(status=200)

    if status == 'AUTHORIZED':
        if order.payment_status != 'paid':
            try:
                tabby.capture_payment(payment_id, order.total)
                order.payment_status = 'paid'
                order.status = 'confirmed'
                order.save()
                _decrement_stock(order)
            except tabby.TabbyError:
                pass
    elif status == 'CLOSED':
        if order.payment_status != 'paid':
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.save()
            _decrement_stock(order)
    elif status in ('REJECTED', 'EXPIRED'):
        order.payment_status = 'failed'
        order.save()

    return HttpResponse(status=200)


def _find_tap_order(request):
    tap_charge_id = request.GET.get('tap_id')
    order = None
    if tap_charge_id:
        order = Order.objects.filter(tap_charge_id=tap_charge_id).order_by('-id').first()
    if order is None:
        # Fallback: the most recent Tap order this browser session created,
        # in case Tap's redirect doesn't carry the tap_id query param.
        granted = request.session.get(ORDER_ACCESS_SESSION_KEY, [])
        order = Order.objects.filter(
            order_number__in=granted, payment_method='tap',
        ).order_by('-id').first()
    return order


def tap_return(request):
    """Tap uses a single redirect URL for every outcome (success, failure,
    cancel) — we tell them apart by re-fetching the charge's status.
    """
    order = _find_tap_order(request)
    if order is None:
        messages.error(request, 'Order not found.')
        return redirect('cart:cart')

    if order.payment_status == 'paid':
        return redirect('orders:order_confirmation', order_number=order.order_number)

    try:
        charge = tap.get_charge(order.tap_charge_id)
        status = charge.get('status')
    except tap.TapError:
        status = None

    if status == 'CAPTURED':
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        _decrement_stock(order)
        _grant_order_access(request, order.order_number)
        CartService(request).clear()
        return redirect('orders:order_confirmation', order_number=order.order_number)

    if status == 'CANCELLED':
        order.delete()
        messages.info(request, 'Checkout cancelled. Your cart is still saved.')
        return redirect('cart:cart')

    order.payment_status = 'failed'
    order.save()
    _grant_order_access(request, order.order_number)
    messages.error(request, "We couldn't confirm your card payment. Please try another payment method.")
    return redirect('orders:payment_failed', order_number=order.order_number)


@csrf_exempt
def tap_webhook(request):
    """Safety-net webhook: keeps order status correct even if the shopper
    closes the tab before the redirect back to tap_return() completes. The
    status is always re-fetched from Tap rather than trusted from the POST
    body, since this endpoint is unauthenticated.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        body = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)

    charge_id = body.get('id')
    if not charge_id:
        return HttpResponse(status=400)

    order = Order.objects.filter(tap_charge_id=charge_id).order_by('-id').first()
    if order is None:
        return HttpResponse(status=404)

    if order.payment_status == 'paid':
        return HttpResponse(status=200)

    try:
        charge = tap.get_charge(charge_id)
    except tap.TapError:
        return HttpResponse(status=200)

    status = charge.get('status')
    if status == 'CAPTURED':
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        _decrement_stock(order)
    elif status in ('FAILED', 'DECLINED', 'CANCELLED', 'ABANDONED'):
        order.payment_status = 'failed'
        order.save()

    return HttpResponse(status=200)


# --- Nomod Hosted Checkout ------------------------------------------------

NOMOD_RETURN_POLLS = 3
NOMOD_RETURN_POLL_SECONDS = 1.5


def _mark_order_paid(order_pk):
    """Marks an order paid exactly once. The row lock stops the return
    redirect and the webhook (which can arrive together) from both
    confirming the order and decrementing stock twice."""
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_pk)
        if order.payment_status == 'paid':
            return order
        order.payment_status = 'paid'
        order.status = 'confirmed'
        order.save()
        _decrement_stock(order)
    return order


def _mark_order_unpaid(order_pk, cancel=False):
    """Records a failed/cancelled/expired payment, unless the order has
    already been paid (a late failure event must never undo a payment)."""
    with transaction.atomic():
        order = Order.objects.select_for_update().get(pk=order_pk)
        if order.payment_status == 'paid':
            return order
        order.payment_status = 'failed'
        if cancel:
            order.status = 'cancelled'
        order.save()
    return order


def _sync_nomod_order(order):
    """Re-fetches the order's checkout from Nomod and applies its state.
    Returns one of: 'paid', 'pending', 'cancelled', 'expired', 'error'.
    The browser redirect and webhook body are never trusted on their own.
    """
    if order.payment_status == 'paid':
        return 'paid'
    if not order.nomod_checkout_id:
        return 'error'
    try:
        checkout = nomod.get_checkout(order.nomod_checkout_id)
    except nomod.NomodError:
        return 'error'

    status = (checkout.get('status') or '').lower()
    if nomod.is_paid_for_order(checkout, order):
        _mark_order_paid(order.pk)
        return 'paid'
    if status == nomod.STATUS_PAID:
        # Paid, but not for this order's exact amount/currency/reference.
        # Leave it for a human rather than confirming or failing it.
        logger.error('Nomod checkout %s is paid but failed verification for order %s',
                     order.nomod_checkout_id, order.order_number)
        return 'error'
    if status == nomod.STATUS_CANCELLED:
        _mark_order_unpaid(order.pk, cancel=True)
        return 'cancelled'
    if status == nomod.STATUS_EXPIRED:
        _mark_order_unpaid(order.pk, cancel=True)
        return 'expired'
    if status not in nomod.KNOWN_STATUSES:
        logger.warning('Nomod checkout %s for order %s has unrecognised status %r (charges: %s)',
                       order.nomod_checkout_id, order.order_number, status, checkout.get('charges'))
    return 'pending'


def _nomod_return_order(request):
    """The order named in a Nomod redirect, and whether this browser session
    is the one that created it (only then do we show it or clear the cart)."""
    order_number = request.GET.get('order', '')
    order = Order.objects.filter(order_number=order_number, payment_method='nomod').first()
    granted = order is not None and order_number in request.session.get(ORDER_ACCESS_SESSION_KEY, [])
    return order, granted


def _nomod_outcome_redirect(request, order, state):
    if state == 'paid':
        CartService(request).clear()
        return redirect('orders:order_confirmation', order_number=order.order_number)
    if state == 'cancelled':
        messages.info(request, 'Payment cancelled. Your cart is still saved.')
        return redirect('cart:cart')
    # failed / expired / still processing / couldn't verify: payment_failed
    # shows "failed" or "still confirming" based on the order's status.
    return redirect('orders:payment_failed', order_number=order.order_number)


def nomod_success(request):
    order, granted = _nomod_return_order(request)
    if order is None:
        messages.error(request, 'Order not found.')
        return redirect('cart:cart')

    state = _sync_nomod_order(order)
    # Nomod can redirect a moment before the charge settles; give it a few
    # short re-checks before telling the customer it's still processing.
    polls = 0
    while state == 'pending' and polls < NOMOD_RETURN_POLLS:
        time.sleep(NOMOD_RETURN_POLL_SECONDS)
        state = _sync_nomod_order(order)
        polls += 1

    if not granted:
        messages.info(request, 'Thank you. You can check your order status with your order number and email.')
        return redirect('orders:tracking')
    order.refresh_from_db()
    return _nomod_outcome_redirect(request, order, state)


def nomod_failure(request):
    order, granted = _nomod_return_order(request)
    if order is None:
        messages.error(request, 'Your payment was not completed.')
        return redirect('cart:cart')

    state = _sync_nomod_order(order)
    if state == 'pending':
        _mark_order_unpaid(order.pk)
        state = 'failed'

    if not granted:
        return redirect('orders:tracking')
    order.refresh_from_db()
    if state != 'paid':
        messages.error(request, 'Your payment was not completed. Please try again or choose Cash on Delivery.')
    return _nomod_outcome_redirect(request, order, state)


def nomod_cancel(request):
    order, granted = _nomod_return_order(request)
    if order is None:
        messages.info(request, 'Payment cancelled. Your cart is still saved.')
        return redirect('cart:cart')

    state = _sync_nomod_order(order)
    if state == 'pending':
        # The order is kept (marked cancelled) rather than deleted, so a
        # payment that still lands later can be matched to it.
        _mark_order_unpaid(order.pk, cancel=True)
        state = 'cancelled'

    if not granted:
        return redirect('orders:tracking')
    order.refresh_from_db()
    return _nomod_outcome_redirect(request, order, state)


def _order_from_nomod_event(data):
    """Finds our order from a webhook's charge data. Nomod's charge payload
    isn't fully documented, so accept a checkout id or our reference from
    the fields it may appear in."""
    checkout = data.get('checkout')
    metadata = data.get('metadata')
    checkout_ids = {
        data.get('checkout_id'),
        checkout if isinstance(checkout, str) else None,
        checkout.get('id') if isinstance(checkout, dict) else None,
    } - {None, ''}
    references = {
        data.get('reference_id'),
        checkout.get('reference_id') if isinstance(checkout, dict) else None,
        metadata.get('order') if isinstance(metadata, dict) else None,
    } - {None, ''}
    if not checkout_ids and not references:
        return None

    query = Q(nomod_checkout_id__in=checkout_ids) | Q(order_number__in=references, payment_method='nomod')
    return Order.objects.filter(query).exclude(nomod_checkout_id='').order_by('-id').first()


@csrf_exempt
def nomod_webhook(request):
    """Safety net for when the shopper closes the tab before being
    redirected back. The signature is verified, and the order's state is
    always re-fetched from Nomod rather than taken from the payload."""
    if request.method != 'POST':
        return HttpResponse(status=405)
    if not nomod.verify_webhook_signature(request.headers, request.body):
        return HttpResponse(status=401)

    try:
        body = json.loads(request.body)
    except ValueError:
        return HttpResponse(status=400)

    event_type = body.get('type', '')
    data = body.get('data') or {}
    order = _order_from_nomod_event(data) if isinstance(data, dict) else None
    if order is None:
        logger.warning('Nomod webhook %s (%s) did not match an order', body.get('eventId'), event_type)
        return HttpResponse(status=200)

    if event_type == 'charge.refunded':
        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)
            if order.payment_status == 'paid':
                order.payment_status = 'refunded'
                order.status = 'refunded'
                order.save()
        return HttpResponse(status=200)

    _sync_nomod_order(order)
    return HttpResponse(status=200)
