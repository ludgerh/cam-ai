# Generated by Django 4.0.3 on 2022-11-04 18:55

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
#from django.utils.timezone import utc

def fill_table(apps, schema_editor):
  User = apps.get_model("auth", "user")
  if not User.objects.all().count():
    newline = User.objects.create(
      password='pbkdf2_sha256$390000$S1kU2slc9jyJIPerlg0Zke$XhcjiuIc1UQY9GpuGPFFE0YSDaM7blJVxsxSZqfBRZQ=',
      is_superuser=True,
      username='admin',
      first_name='admin',
      last_name='admin',
      email='theo@tester.de',
      is_staff=True,
      is_active=True,
    )
  Worker = apps.get_model("tf_workers", "worker")
  if not Worker.objects.all().count():
    Worker.objects.create(active=True, name='TF-Worker 1')
  School = apps.get_model("tf_workers", "school")
  if not School.objects.all().count():
    School.objects.create(active=True, name='Standard')


class Migration(migrations.Migration):

  initial = True

  dependencies = [
    ('trainers', '0001_initial'),
  ]

  operations = [
    migrations.CreateModel(
      name='worker',
      fields=[
          ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
          ('active', models.BooleanField(default=True)),
          ('name', models.CharField(default='New TF-Worker', max_length=100)),
          ('maxblock', models.IntegerField(default=8)),
          ('timeout', models.FloatField(default=1.0)),
          ('max_nr_models', models.IntegerField(default=64)),
          ('max_nr_clients', models.IntegerField(default=64)),
          ('gpu_sim_loading', models.FloatField(default=0.0)),
          ('gpu_sim', models.FloatField(default=-1.0)),
          ('gpu_nr', models.IntegerField(default=0)),
          ('savestats', models.FloatField(default=0.0)),
          ('use_websocket', models.BooleanField(default=True)),
          ('wsserver', models.CharField(default='wss://django.cam-ai.eu/', max_length=255)),
          ('wsname', models.CharField(default='', max_length=50)),
          ('wspass', models.CharField(default='', max_length=50)),
          ('wsid', models.IntegerField(default=0)),
      ],
    ),
    migrations.CreateModel(
      name='school',
      fields=[
          ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
          ('name', models.CharField(max_length=100)),
          ('creator', models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to=settings.AUTH_USER_MODEL)),
          ('dir', models.CharField(default='', max_length=256)),
          ('trigger', models.IntegerField(default=500)),
          ('lastmodelfile', models.DateTimeField(default=datetime.datetime(
            1900, 1, 1, 0, 0, 
            tzinfo=datetime.timezone.utc, 
          ))),
          ('active', models.IntegerField(default=1)),
          ('l_rate_min', models.CharField(default='1e-6', max_length=20)),
          ('l_rate_max', models.CharField(default='1e-6', max_length=20)),
          ('e_school', models.IntegerField(default=1)),
          ('model_type', models.CharField(default='efficientnetv2-b0', max_length=50)),
          ('ignore_checked', models.BooleanField(default=True)),
          ('extra_runs', models.IntegerField(default=0)),
          ('donate_pics', models.BooleanField(default=False)),
          ('weight_max', models.FloatField(default=2.0)),
          ('weight_min', models.FloatField(default=1.0)),
          ('weight_boost', models.FloatField(default=8.0)),
          ('patience', models.IntegerField(default=6)),
          ('tf_worker', models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to='tf_workers.worker')),
          ('trainer', models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to='trainers.trainer')),
      ],
    ),
    migrations.RunPython(fill_table),
  ]
