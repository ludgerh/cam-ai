# Generated by Django 4.0.3 on 2022-11-09 15:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trainers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainer',
            name='wsname',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AddField(
            model_name='trainer',
            name='wspass',
            field=models.CharField(default='', max_length=50),
        ),
        migrations.AlterField(
            model_name='trainer',
            name='t_type',
            field=models.IntegerField(choices=[(1, 'GPU'), (2, 'CPU'), (3, 'Remote'), (4, 'other')], default=3, verbose_name='trainer type'),
        ),
    ]
