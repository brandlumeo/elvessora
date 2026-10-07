from django import template

from products.fragrance_utils import (
    note_icon,
    parse_accords,
    resolve_product_image_url,
    split_notes,
)

register = template.Library()


@register.filter
def split_fragrance_notes(value):
    return split_notes(value)


@register.filter
def fragrance_note_icon(note_name):
    icon_class, color = note_icon(note_name)
    return {'icon': icon_class, 'color': color}


@register.filter
def parse_main_accords(value):
    return parse_accords(value)


@register.simple_tag
def product_image_url(product):
    """Admin-uploaded bottle image first; static SKU art as fallback."""
    return resolve_product_image_url(product)

@register.filter
def product_scent_line(product, max_families=3):
    """Build a scent descriptor line from fragrance families or top notes."""
    families = list(product.fragrance_families.all()[:max_families])
    if families:
        return ' • '.join(f.get_name_display().upper() for f in families)
    notes = split_notes(product.top_notes)
    if notes:
        return ' • '.join(n.strip().upper() for n in notes[:max_families])
    return 'SIGNATURE'


@register.filter
def format_price(value):
    """Format amount as AED (UAE Dirham)."""
    if value is None or value == '':
        return ''
    try:
        amount = int(float(value))
    except (TypeError, ValueError):
        return value
    return f'AED {amount:,}'


@register.filter
def product_short_name(value):
    """Display name without Elvessora prefix. Accepts Product or str."""
    if not value:
        return value
    name = getattr(value, 'name', value)
    if not isinstance(name, str):
        return value
    for prefix in ('Elvessora - ', 'Elvessora '):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name
