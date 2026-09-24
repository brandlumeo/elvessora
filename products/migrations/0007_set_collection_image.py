from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.db import migrations

SOURCE_PATH = Path(settings.BASE_DIR) / 'static' / 'images' / 'products' / 'elvessora-divine-aura.png'


def set_collection_image(apps, schema_editor):
    Collection = apps.get_model('products', 'Collection')

    if not SOURCE_PATH.exists():
        return

    collection = Collection.objects.filter(slug='elvessora-signature').first()
    if not collection or collection.image:
        return

    with open(SOURCE_PATH, 'rb') as f:
        collection.image.save('elvessora-signature-collection.png', File(f), save=True)


def unset_collection_image(apps, schema_editor):
    Collection = apps.get_model('products', 'Collection')
    collection = Collection.objects.filter(slug='elvessora-signature').first()
    if collection and collection.image and 'elvessora-signature-collection' in collection.image.name:
        collection.image.delete(save=True)


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_productfaq'),
    ]

    operations = [
        migrations.RunPython(set_collection_image, unset_collection_image),
    ]
