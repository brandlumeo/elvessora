from django.db import migrations


def clear_hero_image(apps, schema_editor):
    """The hero section's own image was pointing at the same Dubai skyline
    photo now used by the Signature banner right above it — redundant.
    Clear it so the hero falls back to its original static image
    (elvessora-divine-aura-hero.png, the hand-holding-bottle photo)."""
    HomePageContent = apps.get_model('core', 'HomePageContent')
    homepage = HomePageContent.objects.filter(pk=1).first()
    if homepage and homepage.hero_image:
        homepage.hero_image.delete(save=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_fix_shipping_and_remove_vat'),
    ]

    operations = [
        migrations.RunPython(clear_hero_image, noop),
    ]
