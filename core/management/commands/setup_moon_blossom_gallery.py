from django.core.management.base import BaseCommand
from products.models import Product, ProductImage


class Command(BaseCommand):
    help = 'Adds the 3 extra lifestyle/campaign photos to the Moon Blossom product gallery'

    def handle(self, *args, **kwargs):
        try:
            product = Product.objects.get(sku='ELV-MOON-001')
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR('Product ELV-MOON-001 (Moon Blossom) not found.'))
            return

        # Keep the existing bottle-only shot as the primary/hero image
        # (order 0); these are added after it as additional gallery images.
        extra_images = [
            ('products/moon-blossom-smoke-scene.jpg', 'Elvessora Moon Blossom with golden smoke'),
            ('products/moon-blossom-floral-stones.jpg', 'Elvessora Moon Blossom among dark florals and stones'),
            ('products/moon-blossom-moonlit-garden.jpg', 'Elvessora Moon Blossom in a moonlit garden scene'),
        ]

        next_order = (
            ProductImage.objects.filter(product=product).order_by('-order').values_list('order', flat=True).first()
        )
        next_order = (next_order or 0) + 1

        added = 0
        for path, alt_text in extra_images:
            _, created = ProductImage.objects.get_or_create(
                product=product,
                image=path,
                defaults={'alt_text': alt_text, 'is_primary': False, 'order': next_order},
            )
            if created:
                added += 1
                next_order += 1

        self.stdout.write(self.style.SUCCESS(
            f'Added {added} new gallery image(s) to {product.name}. '
            f'Total images now: {ProductImage.objects.filter(product=product).count()}'
        ))
