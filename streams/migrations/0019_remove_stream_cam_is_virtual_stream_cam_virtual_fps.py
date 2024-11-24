# Generated by Django 5.1.2 on 2024-11-23 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('streams', '0018_stream_cam_is_virtual'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='stream',
            name='cam_is_virtual',
        ),
        migrations.AddField(
            model_name='stream',
            name='cam_virtual_fps',
            field=models.FloatField(default=0.0),
        ),
    ]
