# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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

from django.conf import settings
from django_registration.backends.activation.views import ActivationView, RegistrationView
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User
from users.models import userinfo

class MyActivationView(ActivationView):
  def activate(self, *args, **kwargs):
    username = super().activate(*args, **kwargs)
    myuser = User.objects.get(username=username)
    myuserinfo = userinfo(user=myuser, allowed_schools=1, allowed_streams=1, pay_tokens=0)
    myuserinfo.save()
    return(username)
    
class MyRegistrationView(RegistrationView):

  def get_email_context(self, activation_key):
    return {
      "activation_key": activation_key,
      "expiration_days": settings.ACCOUNT_ACTIVATION_DAYS,
      "site": settings.CLIENT_URL[:-1],
    }
    
class TermsView(TemplateView):
  template_name = 'django_registration/terms.html'
