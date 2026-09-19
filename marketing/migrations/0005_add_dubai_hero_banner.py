from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import migrations

SOURCE_PATH = Path(settings.BASE_DIR) / 'static' / 'images' / 'hero' / 'elvessora-divine-aura-dubai-hero.jpg'

TITLE = 'A Fragrance for a Brighter You'


def add_banner(apps, schema_editor):
    Banner = apps.get_model('marketing', 'Banner')

    if Banner.objects.filter(title=TITLE, position='hero').exists():
        return
    if not SOURCE_PATH.exists():
        return

    banner = Banner(
        title=TITLE,
        subtitle=(
            'Crafted in Dubai with rare ingredients, Divine Aura carries '
            'the golden hour with you — wherever you go.'
        ),
        link_url='/collection/',
        button_text='Discover the Collection',
        position='hero',
        order=0,
        is_active=True,
    )
    with open(SOURCE_PATH, 'rb') as f:
        banner.image.save('elvessora-divine-aura-dubai-hero.jpg', File(f), save=True)


def remove_banner(apps, schema_editor):
    Banner = apps.get_model('marketing', 'Banner')
    Banner.objects.filter(title=TITLE, position='hero').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0004_add_hero_banners'),
    ]

    operations = [
        migrations.RunPython(add_banner, remove_banner),
    ]
