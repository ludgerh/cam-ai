# Generated by Django 4.2.5 on 2024-03-17 19:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streams', '0009_alter_stream_crypt_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='stream',
            name='eve_shrink_factor',
            field=models.FloatField(default=0.2),
        ),
    ]
