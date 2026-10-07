from django.db import migrations


def ensure_shipping_policy(apps, schema_editor):
    """The footer links to /legal/shipping/, but production had no Shipping
    Policy row, so the page 404'd. Create it if missing (an existing page,
    edited in the admin, is left alone), quoting the live shipping prices."""
    LegalPage = apps.get_model('core', 'LegalPage')
    if LegalPage.objects.filter(page_type='shipping').exists():
        return

    SiteSettings = apps.get_model('core', 'SiteSettings')
    site = SiteSettings.objects.first()
    charge = site.default_shipping_charge if site else 35
    threshold = site.free_shipping_threshold if site else 1999

    LegalPage.objects.create(
        page_type='shipping',
        title='Shipping Policy',
        content=(
            'We deliver across the UAE. Standard shipping is AED {charge:,.0f}, '
            'and shipping is free on orders above AED {threshold:,.0f}. '
            'Orders are usually delivered within 3-5 business days.'
        ).format(charge=charge, threshold=threshold),
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_clear_hero_image'),
    ]

    operations = [
        migrations.RunPython(ensure_shipping_policy, noop),
    ]
