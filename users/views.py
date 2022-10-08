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
    })
    return context
