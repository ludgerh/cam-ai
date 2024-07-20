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

class status_line(models.Model):
  made = models.DateTimeField()
  events_frames_correct = models.BigIntegerField(default=0) 
  events_frames_missingframes = models.BigIntegerField(default=0)
  eframes_correct = models.BigIntegerField(default=0)
  eframes_missingdb = models.BigIntegerField(default=0)
  eframes_missingfiles = models.BigIntegerField(default=0)
  video_correct = models.BigIntegerField(default=0)
  video_temp = models.BigIntegerField(default=0)
  video_missingdb = models.BigIntegerField(default=0)
  video_missingfiles = models.BigIntegerField(default=0)
  trainer_correct = models.BigIntegerField(default=0)
  trainer_missingdb = models.BigIntegerField(default=0)
  trainer_missingfiles = models.BigIntegerField(default=0)

  def __str__(self):
    return('Cleanup model line: status')

class files_to_delete(models.Model):
  name = models.CharField(max_length=256)

  def __str__(self):
    return('Cleanup model line: files_to_delete')
