from django.db import models

class view_log(models.Model):
  v_type = models.CharField(max_length=1)
  v_id =  models.IntegerField()
  start = models.DateTimeField()
  stop = models.DateTimeField()
  user = models.IntegerField()
  active = models.BooleanField(default=True)

  def __str__(self):
    return('view_logs model (TBD ...)')
