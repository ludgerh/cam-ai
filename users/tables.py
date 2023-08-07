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

from django_tables2 import Table, Column, A
from django.utils.html import format_html
from .models import archive

class archivetable(Table):
  nix = Column(empty_values=())

  class Meta:
    model = archive
    template_name = "django_tables2/bootstrap4.html"
    fields = ("nix", "name", "typecode", "made", )

  def render_typecode(self, value):
    if value == 0:
      return('Image')
    elif value == 1:
      return('Video')
    else:
      return('???')

  def render_name(self, value):
    print('*****', value)
    return format_html('<b>{}</b>', value)

  def render_nix(self, value):
    print('*****')
    return('nix1213')

