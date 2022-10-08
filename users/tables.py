from django_tables2 import Table, Column, A
from .models import archive

class archivetable(Table):

  class Meta:
    model = archive
    template_name = "django_tables2/bootstrap4.html"
    fields = ("name", "typecode", "made", )

  def render_typecode(self, value):
    if value == 0:
      return('Image')
    elif value == 1:
      return('Video')
    else:
      return('???')

