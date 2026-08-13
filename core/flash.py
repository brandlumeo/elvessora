from django.contrib import messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe


def notify_product_action(request, *, product_name, action, product_url='', secondary_label='', secondary_url=''):
    """
    Flash a clear toast: which product was added/removed + View links.
    action examples: 'added to cart', 'added to wishlist', 'removed from wishlist'
    """
    name = format_html('<strong>{}</strong>', product_name)
    links = []
    if product_url:
        links.append(format_html('<a href="{}" class="elv-toast-link">View product</a>', product_url))
    if secondary_url and secondary_label:
        links.append(
            format_html('<a href="{}" class="elv-toast-link">{}</a>', secondary_url, secondary_label)
        )
    link_html = mark_safe(' · '.join(str(x) for x in links)) if links else ''
    body = format_html(
        '<span class="elv-toast-text">{} {}.</span>{}',
        name,
        action,
        format_html(' <span class="elv-toast-actions">{}</span>', link_html) if link_html else '',
    )
    level = messages.INFO if 'removed' in action else messages.SUCCESS
    messages.add_message(request, level, body, extra_tags='elv-toast')
