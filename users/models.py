from datetime import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone
from tf_workers.models import school

class userinfo(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  school = models.ForeignKey(school, on_delete=models.SET_NULL, null=True)
  counter = models.IntegerField(default=0)

  def __str__(self):
    return('userinfo model (TBD ...)')

class archive(models.Model):
  typecode =  models.IntegerField(default=0) # 0 -->> Frame (BMP), 1 --> Video (MP4)
  number = models.IntegerField(default=0)
  users = models.ManyToManyField(settings.AUTH_USER_MODEL)
  school = models.ForeignKey(school, on_delete=models.SET_NULL, null=True)
  name = models.CharField(max_length=100)
  made = models.DateTimeField(default=timezone.make_aware(datetime(1900, 1, 1)))

  def __str__(self):
    return('archive model (TBD ...)')
