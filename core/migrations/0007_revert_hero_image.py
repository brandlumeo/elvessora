from django.db import migrations


def clear_hero_image(apps, schema_editor):
    HomePageContent = apps.get_model('core', 'HomePageContent')
    homepage = HomePageContent.objects.filter(pk=1).first()
    if homepage and homepage.hero_image and 'elvessora-divine-aura-dubai-hero' in homepage.hero_image.name:
        homepage.hero_image.delete(save=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_set_hero_image'),
    ]

    operations = [
        migrations.RunPython(clear_hero_image, noop),
    ]
