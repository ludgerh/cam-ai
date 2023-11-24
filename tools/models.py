# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
# More information and komplete source: https://github.com/ludgerh/cam-ai
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

from django.db import models

class setting(models.Model):
  setting =  models.CharField(max_length=100)
  value =  models.CharField(max_length=100)
  comment =  models.CharField(max_length=255)

  def __str__(self):
    return('Setting: ' + self.setting+' = ' + self.value)

class camurl(models.Model):
  type = models.CharField(max_length=100)
  url =  models.CharField(max_length=255)

  def __str__(self):
    return('CamUrl model: ' + self.type+' - ' + self.url)

class token(models.Model):
  passwd = models.CharField(max_length=20)
  made = models.DateTimeField()
  cat = models.CharField(max_length=3, default='NON')
  #'EVR' = Eventer read (from email)
  #'CAR' = Camera view read
  #'DER' = Detector view read
  #'ETR' = Eventer view read
  #'MOD' = Model file download
  idx = models.IntegerField(default=0)
  info = models.CharField(max_length=255, default='...')
  count = models.IntegerField(default=0)
  valid = models.BooleanField(default=True)

  def __str__(self):
    return('Token: ' + self.passwd)

