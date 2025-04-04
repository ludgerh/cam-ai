# Generated by Django 4.0.3 on 2022-11-04 18:55

import datetime
from django.db import migrations, models
import django.db.models.deletion
#from datetime.timezone import utc


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('streams', '0001_initial'),
        ('tf_workers', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='event',
            fields=[
                ('id', models.BigAutoField(
                  auto_created=True, 
                  primary_key=True, 
                  serialize=False, 
                  verbose_name='ID',
                )),
                ('p_string', models.CharField(default='[]', max_length=255)),
                ('start', models.DateTimeField(default=datetime.datetime(
                  1900, 1, 1, 0, 0, 
                  tzinfo=datetime.timezone.utc, 
                ))),
                ('end', models.DateTimeField(default=datetime.datetime(
                  1900, 1, 1, 0, 0, 
                  tzinfo=datetime.timezone.utc, 
                ))),
                ('xmin', models.IntegerField(default=0)),
                ('xmax', models.IntegerField(default=0)),
                ('ymin', models.IntegerField(default=0)),
                ('ymax', models.IntegerField(default=0)),
                ('numframes', models.IntegerField(default=0)),
                ('done', models.BooleanField(default=False)),
                ('videoclip', models.CharField(default='', max_length=256)),
                ('double', models.BooleanField(default=False)),
                ('hasarchive', models.BooleanField(default=False)),
                ('school', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='tf_workers.school')),
            ],
        ),
        migrations.CreateModel(
            name='evt_condition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reaction', models.IntegerField(choices=[(1, 'show frame'), (2, 'send school'), (3, 'record video'), (4, 'send email'), (5, 'alarm')], default=0, verbose_name='reaction')),
                ('and_or', models.IntegerField(choices=[(1, 'and'), (2, 'or')], default=2, verbose_name='and_or')),
                ('c_type', models.IntegerField(choices=[(1, 'any movement detection'), (2, 'x values above or equal y'), (3, 'x values below or equal y'), (4, 'tag x is above or equal y'), (5, 'tag x is below or equal y'), (6, 'tag x is in top y')], default=1, verbose_name='c_type')),
                ('x', models.IntegerField(default=1, verbose_name='x')),
                ('y', models.FloatField(default=0.5, verbose_name='y')),
                ('bracket', models.IntegerField(default=0, verbose_name='bracket')),
                ('eventer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='streams.stream')),
            ],
        ),
        migrations.CreateModel(
            name='event_frame',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(default=datetime.datetime(
                  1900, 1, 1, 0, 0, 
                  tzinfo=datetime.timezone.utc, 
                ))),
                ('status', models.SmallIntegerField(default=0)),
                ('name', models.CharField(max_length=100)),
                ('x1', models.IntegerField(default=0)),
                ('x2', models.IntegerField(default=0)),
                ('y1', models.IntegerField(default=0)),
                ('y2', models.IntegerField(default=0)),
                ('trainframe', models.BigIntegerField(default=0)),
                ('hasarchive', models.BooleanField(default=False)),
                ('event', models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='eventers.event')),
            ],
        ),
    ]
