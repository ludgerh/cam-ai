from django.db import models

class tag(models.Model):
  name =  models.CharField(max_length=100)
  description = models.CharField(max_length=100)
  school = models.SmallIntegerField(default=0)
  replaces = models.SmallIntegerField(default=-1)

  def __str__(self):
    return(self.name)
