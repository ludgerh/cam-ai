# Generated by Django 5.1.2 on 2025-02-21 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tf_workers', '0033_remove_school_l_rate_decrement_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='school',
            name='l_rate_ini_div',
        ),
        migrations.RemoveField(
            model_name='school',
            name='l_rate_ini_done',
        ),
        migrations.AlterField(
            model_name='school',
            name='l_rate_divisor',
            field=models.FloatField(default=0.0),
        ),
        migrations.AlterField(
            model_name='school',
            name='l_rate_last',
            field=models.FloatField(default=0.01),
        ),
    ]
