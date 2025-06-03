"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
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

from django.urls import path
from django.views.generic.base import TemplateView
from . import views

app_name = 'accounts'

urlpatterns = [
  # Registration & Activation
  path(
    "register/", 
    views.MyRegistrationView.as_view(), 
    name="django_registration_register",
  ),
  path(
    "register/complete/", 
    TemplateView.as_view(template_name="registration/registration_complete.html"), 
    name="django_registration_complete",
  ),
  path(
    "activate/",
    views.MyActivationView.as_view(),
    name="django_registration_activate",
  ),
  path(
    "activate/complete/", 
    TemplateView.as_view(template_name="registration/activation_complete.html"), 
    name="django_registration_activation_complete", 
  ),
  path(
    "activate/<activation_key>/",
    views.MyActivationView.as_view(),
    name="django_registration_activate",
  ),
  path("terms/", 
    TemplateView.as_view(template_name="registration/terms.html"), 
    name="django_terms_view",
  ),
  path("privacy/", 
    TemplateView.as_view(template_name="registration/privacy.html"), 
    name="django_privacy_view",
  ),
  # Auth
  path(
    "login/", 
    views.MyLoginView.as_view(), 
    name="login",
  ),
  path(
    "logout/", 
    views.MyLogoutView.as_view(), 
    name="logout",
  ),
  path(
    "password_reset/", 
    views.MyPasswordResetView.as_view(), 
    name="password_reset",
  ),
  path(
    "password_reset/done/", 
    views.MyPasswordResetDoneView.as_view(), 
    name="password_reset_done",
  ),
  path(
    "reset/<uidb64>/<token>/", 
    views.MyPasswordResetConfirmView.as_view(), 
    name="password_reset_confirm",
  ),
  path(
    "reset/done/", 
    views.MyPasswordResetCompleteView.as_view(), 
    name="password_reset_complete",
  ),
]

