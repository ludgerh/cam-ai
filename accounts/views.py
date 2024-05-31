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

from django.conf import settings
from django_registration.backends.activation.views import ActivationView, RegistrationView
from django.contrib.auth.views import (
  PasswordResetView, 
  PasswordResetDoneView, 
  PasswordResetConfirmView, 
  PasswordResetCompleteView,
  LoginView,
)
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User
try:  
  from camai.passwords import emulatestatic
except  ImportError: # can be removed when everybody is up to date
  emulatestatic = False
from tools.l_tools import djconf
from users.models import userinfo

class MyLoginView(LoginView):
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return context

class MyActivationView(ActivationView):
  def activate(self, *args, **kwargs):
    username = super().activate(*args, **kwargs)
    myuser = User.objects.get(username=username)
    myuserinfo = userinfo(user=myuser, allowed_schools=3, allowed_streams=3, pay_tokens=5)
    myuserinfo.save()
    return(username)
    
class MyRegistrationView(RegistrationView):

  def get_email_context(self, activation_key):
    return {
      "activation_key": activation_key,
      "expiration_days": settings.ACCOUNT_ACTIVATION_DAYS,
      "site": settings.CLIENT_URL[:-1],
    }
    
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return context
    
class TermsView(TemplateView):
  template_name = 'django_registration/terms.html'
    
class PrivacyView(TemplateView):
  template_name = 'django_registration/privacy.html'
  
class MyPasswordResetView(PasswordResetView): 
  template_name = "registration/c_password_reset_form.html"
  success_url = "/accounts/pass_reset/done/"
  
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return context
  
class MyPasswordResetDoneView(PasswordResetDoneView): 
  template_name = "registration/c_password_reset_done.html"
  
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return context
  
class MyPasswordResetConfirmView(PasswordResetConfirmView): 
  template_name = "registration/c_password_reset_confirm.html"
  success_url = "/accounts/reset/complete/"
  
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return context
  
class MyPasswordResetCompleteView(PasswordResetCompleteView): 
  template_name = "registration/c_password_reset_complete.html"
  
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return context
