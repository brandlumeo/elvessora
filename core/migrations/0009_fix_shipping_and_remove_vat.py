from django.db import migrations


def fix_pricing(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    SiteSettings.objects.update(default_shipping_charge=35, tax_rate=0)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_set_hero_image_dubai'),
    ]

    operations = [
        migrations.RunPython(fix_pricing, noop),
    ]
