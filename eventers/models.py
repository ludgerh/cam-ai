from django.db import models
from django.utils import timezone
from datetime import datetime
from django.conf import settings
from tf_workers.models import school
from streams.models import stream

class event(models.Model):
  p_string = models.CharField(max_length=255, default='[]')
  start = models.DateTimeField(default=timezone.make_aware(datetime(1900, 1, 1)))
  end = models.DateTimeField(default=timezone.make_aware(datetime(1900, 1, 1)))
  xmin = models.IntegerField(default=0)
  xmax = models.IntegerField(default=0)
  ymin = models.IntegerField(default=0)
  ymax = models.IntegerField(default=0)
  numframes = models.IntegerField(default=0)
  school = models.ForeignKey(school, on_delete=models.CASCADE, default=1)
  locktime = models.DateTimeField(default=None, null=True)
  done = models.BooleanField(default=False)
  videoclip = models.CharField(max_length=256, default='')
  double = models.BooleanField(default=False)
  hasarchive = models.BooleanField(default=False)

  def __str__(self):
    return('event model, id = '+str(self.id))
	
class event_frame(models.Model):
  time = models.DateTimeField(default=timezone.make_aware(datetime(1900, 1, 1)))
  status = models.SmallIntegerField(default=0)
  name = models.CharField(max_length=100)
  x1 = models.IntegerField(default=0)
  x2 = models.IntegerField(default=0)
  y1 = models.IntegerField(default=0)
  y2 = models.IntegerField(default=0)
  event = models.ForeignKey(event, on_delete=models.CASCADE, default=1)
  trainframe = models.BigIntegerField(default=0)
  hasarchive = models.BooleanField(default=False)

  def __str__(self):
    return('event_frames model (TBD ...)')

class evt_condition(models.Model):
	eventer = models.ForeignKey(stream, on_delete=models.CASCADE)
	reaction = models.IntegerField("reaction", choices=(
		(1, 'show frame'),
		(2, 'send school'),
		(3, 'record video'),
		(4, 'send email'),
		(5, 'alarm'),
	), default=0)
	and_or = models.IntegerField("and_or", choices=((0, 'and'), (1, 'or')), default=0)
	c_type = models.IntegerField("c_type", choices=(
		(1, 'any movement detection'),
		(2, 'x values above or equal y'),
		(3, 'x values below or equal y'),
		(4, 'tag x is above or equal y'),
		(5, 'tag x is below or equal y'),
		(6, 'tag x is in top y'),
	), default=1)
	x = models.IntegerField("x", default=1)
	y = models.FloatField("y", default=0.5)

	def __str__(self):
		return('evt_conditions model (TBD ...)')
