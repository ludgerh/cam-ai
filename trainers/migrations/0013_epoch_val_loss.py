# Generated by Django 5.1.2 on 2024-10-31 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainers', '0012_rename_cmetrics_epoch_binacc_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='epoch',
            name='val_loss',
            field=models.FloatField(default=0),
        ),
    ]
