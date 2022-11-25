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

from django.conf import settings
from django.http import HttpResponse
from django_tables2 import SingleTableView
from access.c_access import access
from tools.l_tools import djconf
from tf_workers.models import school
from .models import archive as dbarchive
from .tables import archivetable

from traceback import format_exc


class archive(SingleTableView):
  model = dbarchive
  table_class = archivetable
  template_name = 'users/archive.html'
  
  def get(self, request, *args, **kwargs):
    self.request = request
    self.schoolnr = kwargs['schoolnr']
    if access.check('S', self.schoolnr, request.user, 'R'):
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))


  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : djconf.getconfigbool('emulatestatic', False),
      'debug' : settings.DEBUG,
      'school' : school.objects.get(id=self.schoolnr),
      'user' : self.request.user,
    })
    return context
