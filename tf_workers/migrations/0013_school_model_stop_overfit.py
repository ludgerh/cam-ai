# Generated by Django 4.2.5 on 2023-11-18 17:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tf_workers', '0012_school_model_xin_school_model_yin'),
    ]

    operations = [
        migrations.AddField(
            model_name='school',
            name='model_stop_overfit',
            field=models.BooleanField(default=True),
        ),
    ]
