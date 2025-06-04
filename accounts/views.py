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

from django.conf import settings
from django.shortcuts import redirect
from django_registration.backends.activation.views import ActivationView, RegistrationView
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import (
  AuthenticationForm, PasswordResetForm, SetPasswordForm,
)
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from camai.c_settings import safe_import
from tools.l_tools import djconf
from users.models import userinfo
from .forms import MyRegistrationFormUniqueEmail

emulatestatic = safe_import('emulatestatic') 

class MyRegistrationView(RegistrationView):
  form_class = MyRegistrationFormUniqueEmail
  success_url = reverse_lazy("accounts:django_registration_complete")
  template_name = "registration/registration_form.html"
  email_subject_template = "registration/activation_email_subject.txt"
  email_body_template = "registration/activation_email_body.txt"

  def get_email_context(self, activation_key):
    context = super().get_email_context(activation_key)
    context.update({
      'site': settings.CLIENT_URL[:-1],
    })
    return(context)
    
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
      'site': settings.CLIENT_URL[:-1],
    })
    return(context)
    
  def send_activation_email(self, user):
    from tools.l_smtp import async_sendmail
    activation_key = self.get_activation_key(user)
    userinfo.objects.get_or_create(
      user=user,
      defaults={
        'allowed_schools' : 3,
        'allowed_streams': 3,
        'pay_tokens': 5,
        'activation_key' : activation_key,
      }
    )
    context = self.get_email_context(activation_key)
    context["user"] = user
    subject = render_to_string(
      template_name=self.email_subject_template,
      context=context,
      request=self.request,
    )
    subject = "".join(subject.splitlines())
    message = render_to_string(
      template_name=self.email_body_template,
      context=context,
      request=self.request,
    )
    async_sendmail(user.email, subject, message)
        
class MyActivationView(ActivationView):
  success_url = reverse_lazy("accounts:django_registration_activation_complete")
  
  def get(self, request, *args, **kwargs):
    activation_key = kwargs.get('activation_key')
    user = userinfo.objects.get(activation_key=activation_key).user
    user.is_active = True
    user.save()
    return redirect(self.success_url)

class MyLoginView(auth_views.LoginView):
  template_name = "auth/login.html"
  authentication_form = AuthenticationForm
    
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return(context)

class MyLogoutView(auth_views.LogoutView):
  next_page = reverse_lazy("accounts:login")

class MyPasswordResetForm(PasswordResetForm):

  #def save(self, domain_override=None, use_https=False, token_generator=None,
  #    from_email=None, request=None, html_email_template_name=None, 
  #    extra_email_context=None):
  def save(self, *args, ** kwargs):
    print('**********', args, kwargs)
      
    email = self.cleaned_data["email"]
    for user in self.get_users(email):
      from django.utils.http import urlsafe_base64_encode
      from django.utils.encoding import force_bytes
      from django.contrib.auth.tokens import default_token_generator

      uid = urlsafe_base64_encode(force_bytes(user.pk))
      token = default_token_generator.make_token(user)
      url = reverse("accounts:password_reset_confirm", kwargs={"uidb64": uid, "token": token})
      reset_link = kwargs['request'].build_absolute_uri(url)
      
      async_sendmail(
        user.email, 
        "Your password link", 
        f"Reset your Password: {reset_link}",
      )

class MyPasswordResetView(auth_views.PasswordResetView):
  template_name = "auth/password_reset_form.html"
  success_url = reverse_lazy("accounts:password_reset_done")
  form_class = MyPasswordResetForm

class MyPasswordResetDoneView(auth_views.PasswordResetDoneView):
  template_name = "auth/password_reset_done.html"
    
  def get_context_data(self, *args, **kwargs):
    context = super().get_context_data(*args, **kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'), 
      'emulatestatic' : emulatestatic,
    })
    return(context)

class MyPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
  template_name = "registration/password_reset_confirm.html"
  success_url = reverse_lazy("accounts:password_reset_complete")
  form_class = SetPasswordForm

class MyPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
  template_name = "registration/password_reset_complete.html"
    
