"""Fragrance note icons, accord helpers, and product image mappings."""

PRODUCT_STATIC_IMAGES = {
    'ELV-MOON-001': 'images/products/elvessora-moon-blossom.png',
    'ELV-SECRET-002': 'images/products/elvessora-secret-romance.png',
    'ELV-AMBER-003': 'images/products/elvessora-amber-petals.png',
    'ELV-ENCHANT-004': 'images/products/elvessora-enchante-bloom.png',
    'ELV-DIVINE-005': 'images/products/elvessora-divine-aura.png',
}

SIGNATURE_SKUS = list(PRODUCT_STATIC_IMAGES.keys())

NOTE_ICONS = {
    'apple': ('bi-apple', '#e8a598'),
    'sweet apple': ('bi-apple', '#e8a598'),
    'bergamot': ('bi-brightness-high', '#f4d03f'),
    'pear': ('bi-circle-fill', '#c8e6c9'),
    'pink pepper': ('bi-circle-fill', '#ef9a9a'),
    'red berries': ('bi-circle-fill', '#c62828'),
    'red fruits': ('bi-circle-fill', '#d32f2f'),
    'mandarin': ('bi-circle-fill', '#ff9800'),
    'lavender': ('bi-flower1', '#9575cd'),
    'watermelon': ('bi-circle-fill', '#ef5350'),
    'sicilian orange': ('bi-circle-fill', '#fb8c00'),
    'orange': ('bi-circle-fill', '#fb8c00'),
    'saffron': ('bi-sun', '#ff8f00'),
    'rose': ('bi-flower2', '#f48fb1'),
    'rose petals': ('bi-flower2', '#f48fb1'),
    'peony': ('bi-flower1', '#f8bbd0'),
    'violet': ('bi-flower1', '#ce93d8'),
    'moonflower': ('bi-moon-stars', '#b39ddb'),
    'white rose': ('bi-flower2', '#fce4ec'),
    'jasmine': ('bi-flower1', '#fff9c4'),
    'jasmine flowers': ('bi-flower1', '#fff9c4'),
    'lily of the valley': ('bi-flower3', '#ffffff'),
    'lotus': ('bi-flower1', '#e1bee7'),
    'orange blossom': ('bi-flower1', '#fff8e1'),
    'vanilla': ('bi-droplet-half', '#d7ccc8'),
    'patchouli': ('bi-tree', '#6d4c41'),
    'musk': ('bi-cloud', '#eceff1'),
    'white musk': ('bi-cloud', '#f5f5f5'),
    'amber': ('bi-gem', '#ff8f00'),
    'soft amber': ('bi-gem', '#ffb74d'),
    'benzoin': ('bi-box', '#a1887f'),
    'cedarwood': ('bi-tree', '#8d6e63'),
    'sandalwood': ('bi-tree', '#a1887f'),
    'ambroxan': ('bi-stars', '#cfd8dc'),
}


def split_notes(notes_string):
    if not notes_string:
        return []
    return [n.strip() for n in notes_string.replace('·', ',').replace('—', ',').split(',') if n.strip()]


def note_icon(note_name):
    key = note_name.lower().strip()
    if key in NOTE_ICONS:
        return NOTE_ICONS[key]
    for partial, icon in NOTE_ICONS.items():
        if partial in key or key in partial:
            return icon
    return ('bi-droplet', '#90a4ae')


def parse_accords(accords_string):
    if not accords_string:
        return []
    result = []
    for part in accords_string.split(','):
        part = part.strip()
        if not part or ':' not in part:
            continue
        name, weight = part.rsplit(':', 1)
        try:
            result.append({'name': name.strip(), 'weight': int(weight.strip())})
        except ValueError:
            continue
    return sorted(result, key=lambda x: x['weight'], reverse=True)


def product_static_image_path(product):
    """Static fallback image path for Elvessora signature products."""
    return PRODUCT_STATIC_IMAGES.get(getattr(product, 'sku', None))


def resolve_product_image_url(product):
    """
    Prefer admin-uploaded ProductImage; fall back to static SKU art.
    Returns an absolute site path (e.g. /media/... or /static/...) or ''.
    """
    from django.templatetags.static import static

    primary = getattr(product, 'primary_image', None)
    if primary and getattr(primary, 'image', None):
        try:
            return primary.image.url
        except (ValueError, AttributeError):
            pass

    static_path = product_static_image_path(product)
    if static_path:
        return static(static_path)
    return ''

