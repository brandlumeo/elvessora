from django.core.management.base import BaseCommand
from products.models import Brand, Product


class Command(BaseCommand):
    help = 'Creates the Elvessora brand record (if missing) and assigns it to every product'

    def handle(self, *args, **kwargs):
        brand, created = Brand.objects.update_or_create(
            name='Elvessora',
            defaults={
                'description': 'Elvessora — luxury fragrances crafted for a personalised scent experience.',
                'is_active': True,
            },
        )
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Found existing"} brand: {brand.name}'))

        updated = Product.objects.filter(brand__isnull=True).update(brand=brand)
        self.stdout.write(self.style.SUCCESS(f'Assigned "{brand.name}" to {updated} product(s) with no brand set.'))

        total = Product.objects.count()
        still_missing = Product.objects.filter(brand__isnull=True).count()
        self.stdout.write(self.style.SUCCESS(
            f'\nDone — {total - still_missing}/{total} products now have a brand assigned.'
        ))
