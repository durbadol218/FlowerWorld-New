# Generated by Django 5.1.3 on 2024-12-15 03:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0021_alter_orderitem_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_transaction_id',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]