# Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
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

from django.urls import path
from django.views.generic.base import TemplateView
from .views import MyActivationView, MyRegistrationView, TermsView, PrivacyView
from .forms import MyRegistrationFormUniqueEmail

app_name = 'accounts'

urlpatterns = [
  path("register/", 
    MyRegistrationView.as_view(form_class=MyRegistrationFormUniqueEmail),
    name="django_registration_register",
  ),
  path("terms/", 
    TermsView.as_view(),
    name="django_terms_view",
  ),
  path("privacy/", 
    PrivacyView.as_view(),
    name="django_privacy_view",
  ),
  path(
    "activate/complete/",
    TemplateView.as_view(
      template_name="django_registration/activation_complete.html"
    ),
    name="django_registration_activation_complete",
  ),
  path(
    "activate/<str:activation_key>/",
    MyActivationView.as_view(),
    name="django_registration_activate",
  ),
]

