from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
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


