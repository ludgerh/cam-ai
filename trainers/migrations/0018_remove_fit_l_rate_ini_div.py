# Generated by Django 5.1.2 on 2025-02-21 12:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trainers', '0017_remove_fit_l_rate_ini_done'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fit',
            name='l_rate_ini_div',
        ),
    ]
