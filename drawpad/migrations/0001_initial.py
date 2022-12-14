# Generated by Django 4.0.3 on 2022-11-04 18:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('streams', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='mask',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mtype', models.CharField(default='X', max_length=1)),
                ('name', models.CharField(default='', max_length=100)),
                ('definition', models.CharField(default='[]', max_length=500)),
                ('stream', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='streams.stream')),
            ],
        ),
    ]
