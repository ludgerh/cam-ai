# Generated by Django 4.0.3 on 2022-11-04 18:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

def fill_table(apps, schema_editor):
  Trainer = apps.get_model("trainers", "trainer")
  if not Trainer.objects.all().count():
    Trainer.objects.create(active=False, name='Trainer 1', gpu_nr=0, running=True)


class Migration(migrations.Migration):

  initial = True

  dependencies = [
      migrations.swappable_dependency(settings.AUTH_USER_MODEL),
  ]

  operations = [
    migrations.CreateModel(
      name='fit',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('made', models.DateTimeField()),
        ('minutes', models.FloatField()),
        ('school', models.IntegerField()),
        ('epochs', models.IntegerField()),
        ('nr_tr', models.IntegerField()),
        ('nr_va', models.IntegerField()),
        ('loss', models.FloatField()),
        ('cmetrics', models.FloatField()),
        ('hit100', models.FloatField(default=0)),
        ('val_loss', models.FloatField()),
        ('val_cmetrics', models.FloatField()),
        ('val_hit100', models.FloatField(default=0)),
        ('cputemp', models.FloatField()),
        ('cpufan1', models.FloatField()),
        ('cpufan2', models.FloatField()),
        ('gputemp', models.FloatField()),
        ('gpufan', models.FloatField()),
        ('description', models.TextField()),
        ('status', models.CharField(default='Done', max_length=10)),
      ],
    ),
    migrations.CreateModel(
      name='trainer',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('active', models.BooleanField(default=True)),
        ('name', models.CharField(default='New Trainer', max_length=256)),
        ('t_type', models.IntegerField(choices=[(1, 'GPU'), (2, 'CPU'), (3, 'Remote'), (4, 'other')], default=3, verbose_name='trainer type')),
        ('gpu_nr', models.IntegerField(default=0, verbose_name='gpu number')),
        ('gpu_mem_limit', models.IntegerField(default=0, verbose_name='gpu mem limit')),
        ('startworking', models.CharField(default='00:00:00', max_length=8)),
        ('stopworking', models.CharField(default='24:00:00', max_length=8)),
        ('running', models.BooleanField(default=False)),
        ('wsserver', models.CharField(default='wss://trainer.cam-ai.eu/', max_length=255)),
        ('wsname', models.CharField(default='', max_length=50)),
        ('wspass', models.CharField(default='', max_length=50)),
      ],
    ),
    migrations.RunPython(fill_table),
    migrations.CreateModel(
      name='trainframe',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('made', models.DateTimeField()),
        ('school', models.SmallIntegerField()),
        ('name', models.CharField(max_length=256)),
        ('code', models.CharField(max_length=2)),
        ('c0', models.SmallIntegerField()),
        ('c1', models.SmallIntegerField()),
        ('c2', models.SmallIntegerField()),
        ('c3', models.SmallIntegerField()),
        ('c4', models.SmallIntegerField()),
        ('c5', models.SmallIntegerField()),
        ('c6', models.SmallIntegerField()),
        ('c7', models.SmallIntegerField()),
        ('c8', models.SmallIntegerField()),
        ('c9', models.SmallIntegerField()),
        ('checked', models.SmallIntegerField()),
        ('train_status', models.SmallIntegerField(default=0)),
        ('made_by', models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
      ],
    ),
    migrations.CreateModel(
      name='epoch',
      fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('seconds', models.FloatField(default=0)),
        ('loss', models.FloatField(default=0)),
        ('cmetrics', models.FloatField(default=0)),
        ('hit100', models.FloatField(default=0)),
        ('val_loss', models.FloatField(default=0)),
        ('val_cmetrics', models.FloatField(default=0)),
        ('val_hit100', models.FloatField(default=0)),
        ('learning_rate', models.FloatField(default=0)),
        ('fit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='trainers.fit')),
      ],
    ),
  ]
