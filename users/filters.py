"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

from django.db.models import Q
from django_filters import FilterSet, CharFilter
from django_filters.views import FilterView
from .models import archive

class myFilterView(FilterView):
    
  def get(self, request, *args, **kwargs):
    filterset_class = self.get_filterset_class()
    self.filterset = self.get_filterset(filterset_class)
    if (not self.filterset.is_bound 
        or self.filterset.is_valid() 
        or not self.get_strict()):
      self.object_list = self.filterset.qs.filter(stream_id=kwargs['streamnr'])
    else:
      self.object_list = self.filterset.queryset.none()
    context = self.get_context_data(filter=self.filterset, object_list=self.object_list)
    return self.render_to_response(context)


class archivefilter(FilterSet):
  filter1 = CharFilter(method='filter1_search', label="Filter:")

  class Meta:
    model = archive
    fields = ['filter1']

  def filter1_search(self, queryset, name, value):
    return archive.objects.filter(Q(name__icontains=value) | Q(made__icontains=value))

