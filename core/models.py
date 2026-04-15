"""
Copyright (C) 2026 by the CAM-AI team, info@cam-ai.de
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

class plugin(models.Model):
  class Type(models.TextChoices):
    ALARM = 'A', 'Alarm'
    DETECTOR = 'D', 'Detector'
    TRAINER = 'T', 'Trainer'
  type = models.CharField(max_length=1, choices=Type.choices)
  default = models.BooleanField(default=False)
  name = models.CharField(max_length=255)
  version = models.CharField(max_length=10)
  maker = models.CharField(max_length=255)
  copyright = models.CharField(max_length=255)
  description  = models.TextField()
  path = models.CharField(max_length=2048)

  def __str__(self):
    return('Plugin model, name: '+self.name)
