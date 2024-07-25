"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
More information and complete source: https://github.com/ludgerh/cam-ai
This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 3
of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful,id
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""

from django.db import models
from streams.models import stream
from tf_workers.models import school

class status_line_event(models.Model):
  made = models.DateTimeField()
  stream = models.ForeignKey(stream, on_delete=models.CASCADE, default=1)
  events_temp = models.BigIntegerField(default=0) 
  events_frames_correct = models.BigIntegerField(default=0) 
  events_frames_missingframes = models.BigIntegerField(default=0)
  eframes_correct = models.BigIntegerField(default=0)
  eframes_missingdb = models.BigIntegerField(default=0)
  eframes_missingfiles = models.BigIntegerField(default=0)

  def __str__(self):
    return('Cleanup model line: status_line_event')

class status_line_video(models.Model):
  made = models.DateTimeField()
  videos_correct = models.BigIntegerField(default=0)
  videos_temp = models.BigIntegerField(default=0)
  videos_missingdb = models.BigIntegerField(default=0)
  videos_missingfiles = models.BigIntegerField(default=0)
  videos_mp4 = models.BigIntegerField(default=0)
  videos_webm = models.BigIntegerField(default=0)
  videos_jpg = models.BigIntegerField(default=0)

  def __str__(self):
    return('Cleanup model line: status_line_video')

class status_line_school(models.Model):
  made = models.DateTimeField()
  school = models.ForeignKey(school, on_delete=models.CASCADE, default=1)
  schools_correct = models.BigIntegerField(default=0)
  schools_missingdb = models.BigIntegerField(default=0)
  schools_missingfiles = models.BigIntegerField(default=0)

  def __str__(self):
    return('Cleanup model line: status_line_school')

class files_to_delete(models.Model):
  name = models.CharField(max_length=256)
  min_age = models.FloatField(default=0.0)

  def __str__(self):
    return('Cleanup model line: files_to_delete')
