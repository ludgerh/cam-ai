# Generated by Django 5.1.2 on 2025-02-22 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tf_workers', '0036_remove_school_l_rate_last_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='l_rate_start',
            field=models.CharField(default='0', max_length=20),
        ),
        migrations.AlterField(
            model_name='school',
            name='l_rate_stop',
            field=models.CharField(default='0', max_length=20),
        ),
    ]
