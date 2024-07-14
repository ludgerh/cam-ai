"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

from django.db import models
from django.conf import settings

class trainer(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=256, default='New Trainer')
  t_type = models.IntegerField("trainer type", choices=((1, 'GPU'), (2, 'CPU'), 
    (3, 'Remote'), (4, 'other')), default=3)
  gpu_nr = models.IntegerField("gpu number", default=1)
  gpu_mem_limit = models.IntegerField("gpu mem limit", default=0)
  startworking = models.CharField(max_length=8, default='00:00:00')
  stopworking = models.CharField(max_length=8, default='24:00:00')
  running  = models.BooleanField(default=False)
  wsserver = models.CharField(max_length=255, default='wss://django.cam-ai.eu/')
  wsname = models.CharField(max_length=50, default='')
  wspass = models.CharField(max_length=50, default='')

  def __str__(self):
    return('Trainer, Name = '+self.name)
    
class img_size(models.Model):
  x = models.IntegerField(default=0)
  y = models.IntegerField(default=0) 

  def __str__(self):
    return('img_size, '+self.x+'x'+self.y)

class trainframe(models.Model):
  deleted = models.BooleanField(default=False)
  made = models.DateTimeField()
  school = models.SmallIntegerField()
  encrypted = models.BooleanField(default=True)
  name =  models.CharField(max_length=256)
  code =  models.CharField(max_length=2)
  c0 = models.SmallIntegerField()
  c1 = models.SmallIntegerField()
  c2 = models.SmallIntegerField()
  c3 = models.SmallIntegerField()
  c4 = models.SmallIntegerField()
  c5 = models.SmallIntegerField()
  c6 = models.SmallIntegerField()
  c7 = models.SmallIntegerField()
  c8 = models.SmallIntegerField()
  c9 = models.SmallIntegerField()
  checked = models.SmallIntegerField()
  made_by = models.ForeignKey(settings.AUTH_USER_MODEL, default=None, 
    on_delete=models.SET_NULL, null=True)
  train_status = models.SmallIntegerField(default=0)
  img_sizes = models.ManyToManyField(img_size)

  def __str__(self):
    return('Trainframe, Name = '+self.name)

class fit(models.Model):
  made = models.DateTimeField()
  minutes = models.FloatField(default=0)
  school = models.IntegerField()
  epochs = models.IntegerField(default=0)
  nr_tr = models.IntegerField(default=0)
  nr_va = models.IntegerField(default=0)
  loss = models.FloatField(default=0)
  cmetrics = models.FloatField(default=0)
  hit100 = models.FloatField(default=0)
  val_loss = models.FloatField(default=0)
  val_cmetrics = models.FloatField(default=0)
  val_hit100 = models.FloatField(default=0)
  model_type = models.CharField(max_length=50, default='')
  model_image_augmentation = models.FloatField(default=0.0)
  model_weight_decay = models.FloatField(default=0.0)
  model_weight_constraint = models.FloatField(default=0.0)
  model_dropout = models.FloatField(default=0.0)
  model_stop_overfit = models.BooleanField(default=True)
  l_rate_start = models.CharField(max_length=20, default='0')
  l_rate_stop = models.CharField(max_length=20, default='0')
  l_rate_delta_min = models.FloatField(default=0.0)
  l_rate_patience = models.IntegerField(default=0)
  l_rate_decrement = models.FloatField(default=0.0)
  weight_min = models.FloatField(default=0.0)
  weight_max = models.FloatField(default=0.0)
  weight_boost = models.FloatField(default=0.0)
  early_stop_delta_min = models.FloatField(default=0.0)
  early_stop_patience = models.IntegerField(default=0)
  status = models.CharField(max_length=10, default='Done')

  def __str__(self):
    return('Fit made ' + str(self.made))

class epoch(models.Model):
  fit = models.ForeignKey(fit, on_delete=models.CASCADE)
  seconds = models.FloatField(default=0)
  loss = models.FloatField(default=0)
  cmetrics = models.FloatField(default=0)
  hit100 = models.FloatField(default=0)
  val_loss = models.FloatField(default=0)
  val_cmetrics = models.FloatField(default=0)
  val_hit100 = models.FloatField(default=0)
  learning_rate = models.FloatField(default=0)

  def __str__(self):
    return('epoch model (TBD ...)')
    
class model_type(models.Model):
  name =  models.CharField(max_length=50, default = 'efficientnetv2-b0')  
  x_in_default = models.IntegerField(default=224)
  y_in_default = models.IntegerField(default=224)

  def __str__(self):
    return('model_type, Name = '+self.name)
