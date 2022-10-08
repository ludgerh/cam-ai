from django.urls import path

from .views import trainer, epochs, dashboard

urlpatterns = [
	path('trainer/<int:schoolnr>/', trainer, name='trainer'),
	path('epochs/<int:schoolnr>/<int:fitnr>/', epochs, name='epochs'),
	path('dashboard/<int:schoolnr>/', dashboard, name='dashboard'),
]

