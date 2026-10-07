from django.db import migrations

TAG_NAME = 'Longevity'


def remove_tag(apps, schema_editor):
    """Takes the #Longevity tag off every post, so no article shows the
    button. The tag itself is kept (unused) so this is easy to undo."""
    BlogTag = apps.get_model('blog', 'BlogTag')
    for tag in BlogTag.objects.filter(name=TAG_NAME):
        tag.posts.clear()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_add_gift_guides_post'),
    ]

    operations = [
        migrations.RunPython(remove_tag, migrations.RunPython.noop),
    ]
