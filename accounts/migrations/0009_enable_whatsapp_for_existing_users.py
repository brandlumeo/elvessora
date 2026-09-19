from django.db import migrations


def enable_whatsapp(apps, schema_editor):
    UserProfile = apps.get_model('accounts', 'UserProfile')
    UserProfile.objects.exclude(phone='').update(whatsapp_notifications=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_knownlogin'),
    ]

    operations = [
        migrations.RunPython(enable_whatsapp, noop),
    ]
