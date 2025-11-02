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

from django.db import models
from django.conf import settings
from django.utils import timezone

class trainer(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=256, default='New Trainer')
  t_type = models.IntegerField("trainer type", choices=((1, 'GPU'), (2, 'CPU'), 
    (3, 'Remote'), (4, 'other')), default=2)
  modeltype = models.IntegerField("model type", choices=((1, 'Keras'), (2, 'LiteRT'), 
    (3, 'LiteRTQ')), default=2) #Codes for download: K, L, Q
  gpu_nr = models.IntegerField("gpu number", default=1)
  gpu_mem_limit = models.IntegerField("gpu mem limit", default=0)
  startworking = models.CharField(max_length=8, default='00:00:00')
  stopworking = models.CharField(max_length=8, default='24:00:00')
  running  = models.BooleanField(default=False)
  wsserver = models.CharField(max_length=255, default='wss://django.cam-ai.eu/')
  wsid = models.IntegerField(default=0)
  wsname = models.CharField(max_length=50, default='')
  wspass = models.CharField(max_length=50, default='')

  def __str__(self):
    return('Trainer, Name = '+self.name)
    
class img_size(models.Model):
  x = models.IntegerField(default=0)
  y = models.IntegerField(default=0) 

  def __str__(self):
    return(f"img_size, {self.x}x{self.y}")
    
trainframe_imex = ['made', 'encrypted', 'name', 'code']
for i in range(10):
  trainframe_imex.append(f'c{i}') 
trainframe_imex.append('checked') 
for i in range(10):
  trainframe_imex.append(f'pred{i}') 

class trainframe(models.Model):
  deleted = models.BooleanField(default=False)
  made = models.DateTimeField()
  school = models.IntegerField(default=0)
  encrypted = models.BooleanField(default=True)
  name = models.CharField(max_length=256)
  code = models.CharField(max_length=2)
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
  last_fit = models.IntegerField(default = -1)
  pred0 = models.FloatField(default=0.0)
  pred1 = models.FloatField(default=0.0)
  pred2 = models.FloatField(default=0.0)
  pred3 = models.FloatField(default=0.0)
  pred4 = models.FloatField(default=0.0)
  pred5 = models.FloatField(default=0.0)
  pred6 = models.FloatField(default=0.0)
  pred7 = models.FloatField(default=0.0)
  pred8 = models.FloatField(default=0.0)
  pred9 = models.FloatField(default=0.0)

  def __str__(self):
    return('Trainframe, Name = '+self.name)

  class Meta:
    indexes = [
        models.Index(fields=["name", "school"]),
    ]

class fit(models.Model):
  made = models.DateTimeField(default=timezone.now)
  minutes = models.FloatField(default=0.0)
  school = models.IntegerField()
  epochs = models.IntegerField(default=0)
  nr_tr = models.IntegerField(default=0)
  nr_va = models.IntegerField(default=0)
  loss = models.FloatField(default=0.0)
  binacc = models.FloatField(default=0.0)
  auc = models.FloatField(default=0.0)
  recall = models.FloatField(default=0.0)
  precision = models.FloatField(default=0.0)
  val_loss = models.FloatField(default=0.0)
  val_binacc = models.FloatField(default=0.0)
  val_auc = models.FloatField(default=0.0)
  val_recall = models.FloatField(default=0.0)
  val_precision = models.FloatField(default=0.0)
  model_type = models.CharField(max_length=50, default='')
  model_image_augmentation = models.FloatField(default=0.0)
  model_weight_decay = models.FloatField(default=0.0)
  model_weight_constraint = models.FloatField(default=0.0)
  model_dropout = models.FloatField(default=0.0)
  model_stop_overfit = models.BooleanField(default=True)
  l_rate_start = models.CharField(max_length=20, default='0')
  l_rate_stop = models.CharField(max_length=20, default='0')
  l_rate_divisor = models.FloatField(default=0.0) #learning rate = val_loss / this
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
  seconds = models.FloatField(default=0.0)
  loss = models.FloatField(default=0.0)
  val_loss = models.FloatField(default=0.0)
  binacc = models.FloatField(default=0.0)
  val_binacc = models.FloatField(default=0.0)
  auc = models.FloatField(default=0.0)
  val_auc = models.FloatField(default=0.0)
  recall = models.FloatField(default=0.0)
  val_recall = models.FloatField(default=0.0)
  precision = models.FloatField(default=0.0)
  val_precision = models.FloatField(default=0.0)
  learning_rate = models.FloatField(default=0.0)

  def __str__(self):
    return('epoch model (TBD ...)')
    
class model_type(models.Model):
  name = models.CharField(max_length=50, default = 'efficientnetv2-b0')  
  x_in_default = models.IntegerField(default=224)
  y_in_default = models.IntegerField(default=224)

  def __str__(self):
    return('model_type, Name = '+self.name)
    
class download(models.Model):
  dl_url = models.CharField(max_length=128)
  school = models.IntegerField(default=1)
  model_kat = models.IntegerField("model type", choices=((1, 'Keras'), (2, 'LiteRT'), 
    (3, 'LiteRTQ')), default=2) #Codes for download: K, L, Q
  model_type = models.CharField(max_length=50, default='efficientnetv2-b0') 

  def __str__(self):
    return('Model download, Url = '+self.dl_url)
