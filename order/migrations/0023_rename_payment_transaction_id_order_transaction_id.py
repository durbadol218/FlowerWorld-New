# Generated by Django 5.1.3 on 2024-12-15 03:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0022_alter_order_payment_transaction_id'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='payment_transaction_id',
            new_name='transaction_id',
        ),
    ]
