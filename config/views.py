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

import os
import json
from socket import gaierror
from importlib import reload
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.conf import settings
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.http import HttpResponseRedirect
from camai.c_settings import safe_import
from tools.l_tools import djconf
from tools.l_smtp import l_smtp, l_msg
from access.c_access import access
from streams.models import stream
from tf_workers.models import school
from .forms import smtp_form

emulatestatic = safe_import('emulatestatic') 
test_email = ''

class myTemplateView(LoginRequiredMixin, TemplateView):

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))

class myFormView(LoginRequiredMixin, FormView):

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))

class config(myTemplateView):
  template_name = 'config/config.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        self.request.user, 'R'
      ),
      'detectorlist' : access.filter_items(
        stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', 
        self.request.user, 'R'
      ),
      'eventerlist' : access.filter_items(
        stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', 
        self.request.user, 'R'
      ),
      'schoollist' : access.filter_items(
        school.objects.filter(active=True), 'S', 
        self.request.user, 'R'
      ),
    })
    if 'open' in kwargs:
      context.update({
        'open' : kwargs['open'], 
        'info' : kwargs['info'], 
      })
    else:
      context.update({
        'open' : '', 
        'info' : '', 
      })
    return context

class smtp(myFormView):
  template_name = 'config/smtp.html'
  form_class = smtp_form
  success_url = '/config/config/smtp/success/'
  
  def get(self, request, *args, **kwargs):
    return super().get(request, *args, **kwargs)
    
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({'info': self.kwargs.get('info', '')})
    return context
  
  def get_initial(self):
    return {
      'server' : djconf.getconfig('smtp_server', forcedb=False),
      'account' : djconf.getconfig('smtp_account', forcedb=False),
      'password' : '****', 
      'port' : djconf.getconfigint('smtp_port', forcedb=False),
      'email' : djconf.getconfig('smtp_email', forcedb=False),
      'test_email' : test_email, 
    }
    
  def get_form(self, form_class=None):
    form_data = self.request.session.get('form_data')
    form_errors = self.request.session.get('form_errors')
    if form_class is None:
      form_class = self.get_form_class()
    if form_data:
      form = form_class(data=form_data)
      del self.request.session['form_data']
      if form_errors:
        for field, messages in form_errors.items():
          for message in messages:
            form.add_error(field, message)
        del self.request.session['form_errors']
      return form
    return super().get_form(form_class)
     
  def form_invalid(self, form): 
    self.request.session['form_data'] = self.request.POST.dict()
    self.request.session['form_errors'] = form.errors
    return HttpResponseRedirect('/config/config/smtp/error/')
    
  def form_valid(self, form):
    global test_email
    test_email = form.cleaned_data['test_email']
    if test_email:
      if form.cleaned_data['password'] == '****':
        mailpassword = djconf.getconfig('smtp_password', forcedb=False)
      else:
        mailpassword = form.cleaned_data['password']  
      sender_email = 'CAM-AI SMTP Email Test<' + form.cleaned_data['email'] + '>'
      tested_server =  {
        'host' : form.cleaned_data['server'],
        'port' : form.cleaned_data['port'],
        'user' : form.cleaned_data['account'],
        'password' : mailpassword,
        'sender_email' : sender_email,
      }  
      my_smtp = l_smtp(**tested_server)
      my_msg = l_msg(
        sender_email,
        test_email,
        'CAM-AI Testmail',
        'The sending was successful, the settings are correct.',
      )
      if my_smtp.is_connected():
        my_smtp.sendmail(sender_email, test_email, my_msg)
      my_smtp.quit()  
      if my_smtp.result_code:  
        if my_smtp.result_code == 1:
          form.add_error('server', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        elif my_smtp.result_code == 2:
          form.add_error('server', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        elif my_smtp.result_code == 3:
          form.add_error('port', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        elif my_smtp.result_code == 4:
          form.add_error('account', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        elif my_smtp.result_code == 5:
          form.add_error('server', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        elif my_smtp.result_code == 6:
          form.add_error('server', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        elif my_smtp.result_code == 10001:
          form.add_error('account', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        else: 
          form.add_error('server', str(my_smtp.result_code) + ': ' + my_smtp.answer)
        return self.form_invalid(form)
    changes = {}
    for item in form.cleaned_data.items():
      if item[0] == 'server':
        if item[1] != djconf.getconfig('smtp_server', forcedb=False):
          djconf.setconfig('smtp_server', item[1])
          changes['smtp_server'] = item[1]
      elif item[0] == 'account':
        if item[1] != djconf.getconfig('smtp_account', forcedb=False):
          djconf.setconfig('smtp_account', item[1])
          changes['smtp_account'] = item[1]
      elif item[0] == 'password':
        if item[1] != '****':
          djconf.setconfig('smtp_password', item[1])
          changes['smtp_password'] = item[1]
      elif item[0] == 'port':
        if item[1] != djconf.getconfigint('smtp_port', forcedb=False):
          djconf.setconfigint('smtp_port', item[1])
          changes['smtp_port'] = item[1]
      elif item[0] == 'email':
        if item[1] != djconf.getconfig('smtp_email', forcedb=False):
          djconf.setconfig('smtp_email', item[1])
          changes['smtp_email'] = item[1]
    print('Changes', changes)      
    if changes:
      sourcefile = open('camai/passwords.py', 'r')
      targetfile = open('camai/passwords.py-new', 'w')  
      for line in sourcefile:
        for item in changes.items():
          if line.startswith(item[0]):
            if isinstance(item[1], str):
              line = item[0] + ' = "' + item[1] + '"\n'
            else:  
              line = item[0] + ' = ' + str(item[1]) + '\n'
        targetfile.write(line) 
      sourcefile.close()
      targetfile.close()
      os.remove('camai/passwords.py')
      os.rename('camai/passwords.py-new', 'camai/passwords.py') 
    return super().form_valid(form)

class tags(myTemplateView):
  template_name = 'config/tags.html'
