from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0008_alter_order_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='tap_charge_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('tamara', 'Pay in Installments (Tamara)'), ('tabby', 'Pay in 4 (Tabby)'), ('tap', 'Credit / Debit Card (Tap)'), ('cod', 'Cash on Delivery')], max_length=20),
        ),
    ]
