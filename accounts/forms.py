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

from django import forms
from django.contrib.auth import get_user_model
from django_registration.forms import RegistrationFormUniqueEmail
from django_registration.forms import validators

User = get_user_model()

class MyRegistrationFormUniqueEmail(RegistrationFormUniqueEmail):

  class Meta(RegistrationFormUniqueEmail.Meta):
      fields = [
          User.USERNAME_FIELD,
          User.get_email_field_name(),
          "firstname",
          "lastname",
          "password1",
          "password2",
      ]
      
  firstname = forms.CharField(label = 'Your first name', max_length = 100)
  lastname = forms.CharField(label = 'Your last name', max_length = 100)
  tos = forms.BooleanField(
    widget=forms.CheckboxInput,
    error_messages={"required": validators.TOS_REQUIRED},
  )   
  pp = forms.BooleanField(
    widget=forms.CheckboxInput,
    error_messages={"required": validators.TOS_REQUIRED},
  )
  doi = forms.BooleanField(
    label = 'I agree to recieve emails from the CAM-AI team.',
    widget=forms.CheckboxInput,
    error_messages={"required": validators.TOS_REQUIRED},
  )
  def save(self, commit=True):
    user = super().save(commit=False)
    user.first_name = self.cleaned_data["firstname"]
    user.last_name = self.cleaned_data["lastname"]
    if commit:
      user.save()
      if hasattr(self, "save_m2m"):
        self.save_m2m()
    return user


