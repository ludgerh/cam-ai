# Generated by Django 4.2.5 on 2024-02-21 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventers', '0009_alter_event_xmax_alter_event_xmin_alter_event_ymax_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='video_encrypted',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='event_frame',
            name='encrypted',
            field=models.BooleanField(default=True),
        ),
    ]
