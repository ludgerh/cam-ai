# Generated by Django 4.2.5 on 2023-11-30 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventers', '0003_alarm'),
    ]

    operations = [
        migrations.AddField(
            model_name='alarm',
            name='name',
            field=models.CharField(default='New Alarm', max_length=20),
        ),
    ]
