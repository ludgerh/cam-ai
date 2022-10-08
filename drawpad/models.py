from django.db import models

from streams.models import stream


class mask(models.Model):
  stream = models.ForeignKey(stream, on_delete=models.CASCADE, null=True)
  mtype = models.CharField(max_length=1, default='X')
  name = models.CharField(max_length=100, default='')
  definition = models.CharField(max_length=500, default='[]')

  def __str__(self):
    return('masks model (TBD ...)')
