from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from core.models import SiteSettings
from .models import Order


def _order_print_context(order_id):
    order = get_object_or_404(
        Order.objects.prefetch_related('items'),
        pk=order_id,
    )
    return {
        'order': order,
        'items': order.items.all(),
        'site': SiteSettings.get(),
    }


@staff_member_required
def order_invoice(request, object_id):
    context = _order_print_context(object_id)
    context['doc_title'] = f'Invoice — {context["order"].order_number}'
    return render(request, 'admin/orders/invoice.html', context)


@staff_member_required
def order_packing_slip(request, object_id):
    context = _order_print_context(object_id)
    context['doc_title'] = f'Packing Slip — {context["order"].order_number}'
    return render(request, 'admin/orders/packing_slip.html', context)
