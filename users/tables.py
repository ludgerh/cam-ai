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

from django_tables2 import Table, Column, DateTimeColumn
from django.utils.html import format_html
from .models import archive

class archivetable(Table):
  image = Column(empty_values=())
  made = DateTimeColumn(format ='d. m. Y, H:i')
  typecode = Column(verbose_name='Type' )
  action = Column(empty_values=())

  class Meta:
    model = archive
    template_name = "django_tables2/bootstrap4.html"
    fields = ("image", "name", "typecode", "made", "action")

  def render_typecode(self, value):
    if value == 0:
      return('Image')
    elif value == 1:
      return('Video')
    else:
      return('???')

  def render_image(self, value, record):
    if record.typecode == 0:
      htmlline = '<a href="/schools/getbigbmp/2/' + str(record.id) + '/" target="_blank">'
      htmlline += ('<img style="width: 210px; height: 210px; object-fit: contain" src="'
        + '/schools/getbmp/2/' + str(record.id) + '/3/1/210/210/">')
    elif record.typecode == 1:  
      htmlline = '<a href="/schools/getbigmp4/' + str(record.id) + '/video.html" target="_blank">'
      htmlline += ('<img style="width: 210px; height: 210px; object-fit: contain" src="'
        + '/schools/getbmp/3/' + str(record.id) + '/3/1/210/210/">')
    htmlline +=  '</a><br>' 
    return(format_html(htmlline))

  def render_name(self, value):
    return format_html('<b>{}</b>', value)

  def render_action(self, value, record):
    htmlline = '<div>'
    htmlline += '<button type="button" class="btn btn-primary m-2 delbtn" data-bs-toggle="modal" data-bs-target="#deleteModal" idx="' + str(record.id) + '" style="width: 120px;">Delete</button>'
    htmlline += '</div>'
    htmlline += '<div>'
    htmlline += '<button type="button" class="btn btn-primary m-2 dldbtn" idx="' + str(record.id) + '" style="width: 120px;">Download</button>'
    htmlline += '</div>'
    return format_html(htmlline)
