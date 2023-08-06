# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

from datetime import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone
from tf_workers.models import school

class userinfo(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  made = models.DateTimeField(default=timezone.now)
  allowed_schools = models.IntegerField(default=3)
  allowed_streams = models.IntegerField(default=2)
  pay_tokens = models.IntegerField(default=0)
  deadline = models.DateTimeField(default=timezone.make_aware(datetime(2100, 1, 1)))

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
