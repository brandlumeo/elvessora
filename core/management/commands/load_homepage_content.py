from django.core.management.base import BaseCommand
from core.models import HomePageContent, HomePageHighlight


DEFAULT_HIGHLIGHTS = [
    ('hero_feature', 'bi-flower1', 'Premium Ingredients', ''),
    ('hero_feature', 'bi-clock-history', 'Long Lasting Scent', ''),
    ('hero_feature', 'bi-box-seam', 'Luxury Packaging', ''),
    ('hero_feature', 'bi-heart', 'Cruelty Free & Vegan', ''),
    ('ingredient', 'bi-flower1', 'Rose', 'Elegance'),
    ('ingredient', 'bi-tree', 'Oud', 'Mystery'),
    ('ingredient', 'bi-stars', 'Amber', 'Warmth'),
    ('ingredient', 'bi-droplet-half', 'Vanilla', 'Softness'),
    ('ingredient', 'bi-cloud', 'Musk', 'Depth'),
    ('ingredient', 'bi-sun', 'Jasmine', 'Purity'),
    ('value_prop', 'bi-gem', '100% Premium Ingredients', 'Carefully sourced accords'),
    ('value_prop', 'bi-droplet', 'Fine French Perfume Oils', 'Luxury concentration'),
    ('value_prop', 'bi-clock', 'Lasts Up To 12+ Hours', 'Long-wearing performance'),
]


class Command(BaseCommand):
    help = 'Create or refresh default luxury homepage content.'

    def handle(self, *args, **options):
        content, _ = HomePageContent.objects.get_or_create(pk=1)
        content.hero_title = 'Luxury\nFragrance'
        content.save()
        self.stdout.write('Homepage content ready.')

        HomePageHighlight.objects.all().delete()
        for index, (kind, icon, title, subtitle) in enumerate(DEFAULT_HIGHLIGHTS):
            HomePageHighlight.objects.create(
                highlight_type=kind,
                icon=icon,
                title=title,
                subtitle=subtitle,
                order=index,
                is_active=True,
            )

        self.stdout.write(self.style.SUCCESS(f'Seeded {len(DEFAULT_HIGHLIGHTS)} homepage highlights.'))
