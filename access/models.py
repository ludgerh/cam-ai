"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
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

class access_control(models.Model):
  vtype = models.CharField(max_length=1) # 'C', 'D', 'E', 'S' or '0'
  vid = models.IntegerField()
  u_g = models.CharField(max_length=1, default='U') # 'U' = user, 'G' = group
  u_g_nr = models.IntegerField(default=0) # 0 = all users/groups
  r_w  = models.CharField(max_length=1, default='R') # 'R' = read, 'W' = write, '0' = read and write

  def __str__(self):
    return(self.vtype+'_'+str(self.vid)+' '+self.u_g+'_'+str(self.u_g_nr)+' '+self.r_w)

