# Generated by Django 4.2.5 on 2024-09-15 14:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tf_workers', '0023_alter_school_remote_creator_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='school',
            name='remote_creator',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='remotely_created_schools', to=settings.AUTH_USER_MODEL),
        ),
    ]
