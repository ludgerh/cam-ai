# Generated by Django 5.1.2 on 2024-11-03 19:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tf_workers', '0024_alter_school_remote_creator'),
    ]

    operations = [
        migrations.AddField(
            model_name='worker',
            name='use_rtlite',
            field=models.BooleanField(default=False),
        ),
    ]