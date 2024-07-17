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
  events_frames_missingevents = models.BigIntegerField(default=0) 

  def __str__(self):
    return('Cleanup model line: status')

class events_frames_missingframe(models.Model):
  idx =  models.BigIntegerField()

  def __str__(self):
    return('Cleanup model line: events_frames_missingframe')

class events_frames_missingdbline(models.Model):
  idx =  models.BigIntegerField()

  def __str__(self):
    return('Cleanup model line: events_frames_missingdbline')
