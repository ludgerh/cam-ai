"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""

#rom math import sqrt
from django.db import models
from django.utils import timezone
from datetime import datetime
from django.conf import settings
from trainers.models import trainer as trainermod

class worker(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=100, default='New TF-Worker')
  maxblock = models.IntegerField(default=8)
  timeout = models.FloatField(default=0.1)
  max_nr_models = models.IntegerField(default=64)
  gpu_sim_loading = models.FloatField(default=0.0)
  gpu_sim = models.FloatField(default=-1.0)
  gpu_nr = models.IntegerField(default=0)
  savestats = models.FloatField(default=0.0)
  use_websocket = models.BooleanField(default=False)
  use_litert = models.BooleanField(default=True)
  remote_trainer = models.BooleanField(default=False)
  wsserver = models.CharField(max_length=255, default='wss://django.cam-ai.eu/')
  wsid = models.IntegerField(default=0)
  wsname = models.CharField(max_length=50, default='')
  wspass = models.CharField(max_length=50, default='')

  def __str__(self):
    return('Worker model, TBD')

class school(models.Model):
  name =  models.CharField(max_length=100)
  creator = models.ForeignKey(settings.AUTH_USER_MODEL, 
    on_delete=models.SET_DEFAULT, default=1, related_name='created_schools')
  remote_creator = models.ForeignKey(settings.AUTH_USER_MODEL, 
    on_delete=models.SET_DEFAULT, default=1, related_name='remotely_created_schools')
  storage_quota = models.BigIntegerField(default=1)
  delegation_level = models.IntegerField(default=1)
  encrypted = models.BooleanField(default=True)
  dir = models.CharField(max_length=256, default='data/schools/model1/')
  trigger = models.IntegerField(default=500)
  lastmodelfile = models.DateTimeField(
    default=timezone.make_aware(datetime(1900, 1, 1)))
  active = models.IntegerField(default=1)
  e_school = models.IntegerField(default=1)
  tf_worker = models.ForeignKey(worker, on_delete=models.SET_DEFAULT, default=1)
  trainers = models.ManyToManyField(trainermod)
  ignore_checked = models.BooleanField(default=True)
  trainer_nr = models.IntegerField(default=1)
  donate_pics = models.BooleanField(default=False)
  save_new_model = models.BooleanField(default=True)
  model_type = models.CharField(max_length=50, default='efficientnetv2-b0')
  model_train_type = models.CharField(max_length=50, default='efficientnetv2-b0')
  model_xin = models.IntegerField(default=224)
  model_yin = models.IntegerField(default=224)
  model_image_augmentation = models.FloatField(default=0.2)
  model_weight_decay = models.FloatField(default=0.0)
  model_weight_constraint = models.FloatField(default=0.0)
  model_dropout = models.FloatField(default=0.0)
  model_stop_overfit = models.BooleanField(default=True)
  l_rate_start = models.CharField(max_length=20, default='0')
  l_rate_stop = models.CharField(max_length=20, default='0')
  l_rate_divisor = models.FloatField(default=10000.0) #learning rate = val_loss / this
  weight_min = models.FloatField(default=1.0)
  weight_max = models.FloatField(default=2.0)
  weight_boost = models.FloatField(default=8.0)
  early_stop_delta_min = models.FloatField(default=0.0001)
  early_stop_patience = models.IntegerField(default=7)

  def __str__(self):
    return(self.name)
