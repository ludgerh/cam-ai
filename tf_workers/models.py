from django.db import models
from django.utils import timezone
from datetime import datetime
from trainers.models import trainer as trainermod

class worker(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=100, default='New TF-Worker')
  maxblock = models.IntegerField(default=8)
  timeout = models.FloatField(default=0.1)
  max_nr_models = models.IntegerField(default=64)
  max_nr_clients = models.IntegerField(default=20)
  gpu_sim_loading = models.FloatField(default=0.0)
  gpu_sim = models.FloatField(default=-1.0)
  gpu_nr = models.IntegerField(default=0)
  savestats = models.FloatField(default=0.0)
  use_websocket = models.BooleanField(default=False)
  wsserver = models.CharField(max_length=255, default='')
  wsname = models.CharField(max_length=30, default='')
  wspass = models.CharField(max_length=30, default='')

  def __str__(self):
    return('Worker model, TBD')

class school(models.Model):
  name =  models.CharField(max_length=100)
  dir = models.CharField(max_length=256, default='')
  trigger = models.IntegerField(default=500)
  lastmodelfile = models.DateTimeField(default=timezone.make_aware(datetime(1900, 1, 1)))
  active = models.IntegerField(default=1)
  l_rate_min = models.CharField(max_length=20, default = '-1')
  l_rate_max = models.CharField(max_length=20, default = '-1')
  e_school = models.IntegerField(default=1)
  model_type = models.CharField(max_length=50, default = 'cam-ai_model')
  tf_worker = models.ForeignKey(worker, on_delete=models.SET_DEFAULT, default=1)
  trainer = models.ForeignKey(trainermod, on_delete=models.SET_DEFAULT, default=1)
  ignore_checked = models.BooleanField(default=False)
  extra_runs = models.IntegerField(default=0)
  donate_pics = models.BooleanField(default=True)
  weight_max = models.FloatField(default=2.0)
  weight_min = models.FloatField(default=1.0)
  weight_boost = models.FloatField(default=1.0)
  patience = models.IntegerField(default=6)

  def __str__(self):
    return(self.name)
