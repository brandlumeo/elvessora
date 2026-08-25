"""Product feed exports for manual upload to Amazon.ae Seller Central and
Noon Seller Lab.

These are NOT the official platform templates — Amazon and Noon each publish
their own category-specific bulk-upload template (with mandatory columns that
vary by category and marketplace) from inside your seller dashboard. Download
that template first, then copy/map these columns into it. This export exists
so the underlying data — SKU, price, stock, images, descriptions — comes
straight from Elvessora's catalog instead of being retyped by hand.
"""
import csv
import io

from django.conf import settings

AMAZON_COLUMNS = [
    'sku', 'product-id', 'product-id-type', 'item-name', 'brand', 'manufacturer',
    'item-description', 'standard-price', 'quantity', 'main-image-url',
    'bullet-point1', 'bullet-point2', 'bullet-point3',
]

NOON_COLUMNS = [
    'seller_sku', 'barcode', 'name_en', 'brand', 'category',
    'description', 'price', 'sale_price', 'quantity', 'image_url', 'size',
]


def _absolute_url(path):
    base = getattr(settings, 'SITE_URL', '').rstrip('/')
    if not path:
        return ''
    return f'{base}{path}' if path.startswith('/') else f'{base}/{path}'


def _primary_image_url(product):
    image = product.images.filter(is_primary=True).first() or product.images.first()
    if image and image.image:
        try:
            return _absolute_url(image.image.url)
        except ValueError:
            return ''
    return ''


def _rows_for(product):
    """One row per variant (size), or one row for the product itself if it
    has no variants."""
    variants = list(product.variants.all())
    return variants or [None]


def amazon_feed_rows(products):
    rows = []
    for product in products:
        image_url = _primary_image_url(product)
        brand_name = product.brand.name if product.brand_id else ''
        for variant in _rows_for(product):
            size_suffix = f' {variant.size}' if variant else ''
            rows.append({
                'sku': variant.sku if variant else product.sku,
                'product-id': product.barcode,
                'product-id-type': 'EAN' if product.barcode else '',
                'item-name': f'{product.name}{size_suffix}'.strip(),
                'brand': brand_name,
                'manufacturer': brand_name,
                'item-description': (product.short_description or product.description)[:2000],
                'standard-price': f'{(variant.current_price if variant else product.current_price):.2f}',
                'quantity': variant.stock_quantity if variant else product.total_stock,
                'main-image-url': image_url,
                'bullet-point1': product.main_accords[:500] if product.main_accords else '',
                'bullet-point2': f'Top notes: {product.top_notes}' if product.top_notes else '',
                'bullet-point3': f'{product.get_concentration_display()} — {product.get_gender_display()}',
            })
    return rows


def noon_feed_rows(products):
    rows = []
    for product in products:
        image_url = _primary_image_url(product)
        brand_name = product.brand.name if product.brand_id else ''
        category_name = product.category.name if product.category_id else ''
        for variant in _rows_for(product):
            price = variant.price if variant else product.regular_price
            sale_price = (variant.offer_price if variant else product.offer_price) or ''
            rows.append({
                'seller_sku': variant.sku if variant else product.sku,
                'barcode': product.barcode,
                'name_en': product.name,
                'brand': brand_name,
                'category': category_name,
                'description': (product.short_description or product.description)[:2000],
                'price': f'{price:.2f}',
                'sale_price': f'{sale_price:.2f}' if sale_price else '',
                'quantity': variant.stock_quantity if variant else product.total_stock,
                'image_url': image_url,
                'size': variant.size if variant else '',
            })
    return rows


def write_csv(columns, rows):
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()
