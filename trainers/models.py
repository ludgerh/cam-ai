from django.db import models
from django.conf import settings

class trainer(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=256, default='New Trainer')
  t_type = models.IntegerField("trainer type", choices=((1, 'GPU'), (2, 'CPU'), (3, 'Remote'), (4, 'other')), default=1)
  gpu_nr = models.IntegerField("gpu number", default=1)
  gpu_mem_limit = models.IntegerField("gpu mem limit", default=0)
  startworking = models.CharField(max_length=8, default='00:00:00')
  stopworking = models.CharField(max_length=8, default='24:00:00')
  running  = models.BooleanField(default=False)
  wsserver = models.CharField(max_length=255, default='')

  def __str__(self):
    return('Trainer, Name = '+self.name)


class trainframe(models.Model):
  made = models.DateTimeField()
  school = models.SmallIntegerField()
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
  made_by = models.ForeignKey(settings.AUTH_USER_MODEL, default=None, on_delete=models.SET_NULL, null=True)
  train_status = models.SmallIntegerField(default=0)

  def __str__(self):
    return('Trainframe, Name = '+self.name)

class fit(models.Model):
  made = models.DateTimeField()
  minutes = models.FloatField()
  school = models.IntegerField()
  epochs = models.IntegerField()
  nr_tr = models.IntegerField()
  nr_va = models.IntegerField()
  loss = models.FloatField()
  cmetrics = models.FloatField()
  hit100 = models.FloatField(default=0)
  val_loss = models.FloatField()
  val_cmetrics = models.FloatField()
  val_hit100 = models.FloatField(default=0)
  cputemp = models.FloatField()
  cpufan1 = models.FloatField()
  cpufan2 = models.FloatField()
  gputemp = models.FloatField()
  gpufan = models.FloatField()
  description = models.TextField()
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
