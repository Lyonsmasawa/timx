# Generated by Django 4.2.17 on 2025-03-05 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('device', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='device',
            name='device_id',
        ),
        migrations.AddField(
            model_name='device',
            name='active',
            field=models.BooleanField(default=False),
        ),
    ]
