from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import migrations

SOURCE_PATH = Path(settings.BASE_DIR) / 'static' / 'images' / 'hero' / 'elvessora-divine-aura-dubai-hero.jpg'


def set_hero_image(apps, schema_editor):
    HomePageContent = apps.get_model('core', 'HomePageContent')

    if not SOURCE_PATH.exists():
        return

    homepage, _ = HomePageContent.objects.get_or_create(pk=1)

    with open(SOURCE_PATH, 'rb') as f:
        homepage.hero_image.save('elvessora-divine-aura-dubai-hero.jpg', File(f), save=True)


def unset_hero_image(apps, schema_editor):
    HomePageContent = apps.get_model('core', 'HomePageContent')
    homepage = HomePageContent.objects.filter(pk=1).first()
    if homepage and homepage.hero_image and 'elvessora-divine-aura-dubai-hero' in homepage.hero_image.name:
        homepage.hero_image.delete(save=True)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_faq_category'),
    ]

    operations = [
        migrations.RunPython(set_hero_image, unset_hero_image),
    ]
