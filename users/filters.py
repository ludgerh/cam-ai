from decimal import Decimal
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
      self.object_list = self.filterset.qs.filter(school=kwargs['schoolnr'])
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

