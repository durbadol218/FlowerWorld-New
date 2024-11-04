# Generated by Django 5.1 on 2024-09-05 03:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flowers', '0002_alter_flowercategory_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='flower',
            name='category',
        ),
        migrations.AddField(
            model_name='flower',
            name='category',
            field=models.ManyToManyField(related_name='flowers', to='flowers.flowercategory'),
        ),
    ]
