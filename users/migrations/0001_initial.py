# Generated by Django 4.0.3 on 2022-11-04 18:55

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import now

def fill_table(apps, schema_editor):
  User = apps.get_model("auth", "user")
  Userinfo = apps.get_model("users", "userinfo")
  myuser = User.objects.first()
  if not Userinfo.objects.all().count():
    Userinfo.objects.create(user_id=myuser.id)


class Migration(migrations.Migration):

  initial = True

  dependencies = [
    ('tf_workers', '0001_initial'),
    migrations.swappable_dependency(settings.AUTH_USER_MODEL),
  ]

  operations = [
    migrations.CreateModel(
      name='userinfo',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
        ('allowed_schools', models.IntegerField(default=3)),
        ('allowed_streams', models.IntegerField(default=3)),
        ('deadline', models.DateTimeField(default=datetime.datetime(
          2100, 1, 1, 0, 0, 
          tzinfo=datetime.timezone.utc, 
        ))),
        ('made', models.DateTimeField(default=now)),
        ('pay_tokens', models.IntegerField(default=0)),
      ],
    ),
    migrations.RunPython(fill_table),
    migrations.CreateModel(
      name='archive',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('typecode', models.IntegerField(default=0)),
        ('number', models.IntegerField(default=0)),
        ('name', models.CharField(max_length=100)),
        ('made', models.DateTimeField(default=datetime.datetime(
          1900, 1, 1, 0, 0, 
          tzinfo=datetime.timezone.utc, 
        ))),
        ('school', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='tf_workers.school')),
        ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL)),
      ],
    ),
  ]
