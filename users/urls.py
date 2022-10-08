from django.urls import path

from .views import archive

urlpatterns = [
	path('archive/<int:schoolnr>/', archive.as_view(), name='archive'),
]

