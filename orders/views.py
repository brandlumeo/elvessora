from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
import razorpay
import hmac
import hashlib

from cart.cart_service import CartService
from core.models import SiteSettings
from .forms import CheckoutForm
from .models import Order, OrderItem, Coupon, Payment


def checkout(request):
    cart_service = CartService(request)
    cart = cart_service.cart
    if not cart.items.exists():
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:shop')

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
            payment_method=form.cleaned_data['payment_method'],
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
            if item.variant:
                item.variant.stock_quantity = max(0, item.variant.stock_quantity - item.quantity)
                item.variant.save()

        if coupon:
            coupon.used_count += 1
            coupon.save()

        request.session.pop('coupon_code', None)

        if form.cleaned_data['payment_method'] == 'cod':
            order.payment_status = 'pending'
            order.status = 'confirmed'
            order.save()
            cart_service.clear()
            messages.success(request, f'Order {order.order_number} placed successfully!')
            return redirect('orders:order_confirmation', order_number=order.order_number)

        if settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET:
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
            return render(request, 'orders/payment.html', {
                'order': order,
                'razorpay_key': settings.RAZORPAY_KEY_ID,
                'amount': int(order.total * 100),
            })

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

        generated = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode(),
            f'{order_id}|{payment_id}'.encode(),
            hashlib.sha256,
        ).hexdigest()

        order = get_object_or_404(Order, razorpay_order_id=order_id)
        if hmac.compare_digest(generated, signature or ''):
            order.payment_status = 'paid'
            order.status = 'confirmed'
            order.razorpay_payment_id = payment_id
            order.save()
            payment = order.payment
            payment.razorpay_payment_id = payment_id
            payment.razorpay_signature = signature
            payment.status = 'paid'
            payment.save()
            CartService(request).clear()
            return redirect('orders:order_confirmation', order_number=order.order_number)

        order.payment_status = 'failed'
        order.save()
        messages.error(request, 'Payment verification failed.')
        return redirect('orders:payment_failed', order_number=order.order_number)

    return redirect('cart:cart')


def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/confirmation.html', {'order': order})


def payment_failed(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    return render(request, 'orders/payment_failed.html', {'order': order})


def order_tracking(request):
    order_number = request.GET.get('order_number', '')
    email = request.GET.get('email', '')
    order = None
    if order_number:
        qs = Order.objects.filter(order_number=order_number)
        if email:
            qs = qs.filter(guest_email=email) | qs.filter(user__email=email)
        order = qs.first()
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
