# Generated by Django 4.0.3 on 2022-11-23 14:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trainers', '0006_trainer_wsadminpass'),
    ]

    operations = [
        migrations.DeleteModel(
            name='client',
        ),
        migrations.RemoveField(
            model_name='trainer',
            name='wsadminpass',
        ),
    ]
