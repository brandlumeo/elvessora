from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_alter_productvariant_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='main_accords',
            field=models.CharField(
                blank=True,
                help_text='Format: accord:weight,accord:weight (e.g. floral:90,vanilla:75)',
                max_length=500,
            ),
        ),
    ]
