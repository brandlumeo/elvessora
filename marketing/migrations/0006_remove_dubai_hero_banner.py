from django.db import migrations

TITLE = 'A Fragrance for a Brighter You'


def remove_banner(apps, schema_editor):
    Banner = apps.get_model('marketing', 'Banner')
    Banner.objects.filter(title=TITLE, position='hero').delete()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0005_add_dubai_hero_banner'),
    ]

    operations = [
        migrations.RunPython(remove_banner, noop),
    ]
