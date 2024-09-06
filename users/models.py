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

from datetime import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone
from streams.models import stream

class userinfo(models.Model):
  user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
  made = models.DateTimeField(default=timezone.now)
  allowed_schools = models.IntegerField(default=3)
  allowed_streams = models.IntegerField(default=3)
  pay_tokens = models.IntegerField(default=5)
  deadline = models.DateTimeField(default=timezone.make_aware(datetime(2100, 1, 1)))
  storage_quota = models.BigIntegerField(default=1000000000)
  storage_used = models.BigIntegerField(default=0)
  mail_flag_quota75 = models.BooleanField(default=False)
  mail_flag_quota100 = models.BooleanField(default=False)
  mail_flag_discspace95 = models.BooleanField(default=False)

  def __str__(self):
    return(self.user.username + ' (userinfo model)')

class archive(models.Model):
  typecode =  models.IntegerField(default=0) # 0 -->> Frame (BMP), 1 --> Video (MP4)
  number = models.IntegerField(default=0)
  users = models.ManyToManyField(settings.AUTH_USER_MODEL)
  stream = models.ForeignKey(stream, on_delete=models.SET_NULL, null=True)
  name = models.CharField(max_length=100)
  made = models.DateTimeField(default=timezone.make_aware(datetime(1900, 1, 1)))

  def __str__(self):
    return('archive model (TBD ...)')
