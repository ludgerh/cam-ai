from django.urls import path
from .views import health

app_name = 'tools'

urlpatterns = [
	path('health/', health.as_view(), name='health'),
]

