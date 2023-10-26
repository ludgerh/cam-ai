# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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

from streams.models import stream


class mask(models.Model):
  stream = models.ForeignKey(stream, on_delete=models.CASCADE, null=True)
  # C: Cam mask X: unscaled Detector mask, D: scaled Dector mask
  mtype = models.CharField(max_length=1, default='C')
  name = models.CharField(max_length=100, default='')
  definition = models.CharField(max_length=500, default='[]')

  def __str__(self):
    return('masks model (TBD ...)')
