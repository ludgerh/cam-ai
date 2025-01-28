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
from django import forms

class smtp_form(forms.Form):
  server = forms.CharField(label="SMTP server", max_length=100)
  account = forms.CharField(label="SMTP account", max_length=100)
  password = forms.CharField(label="SMTP password", max_length=100)
  port = forms.IntegerField(label="SMTP port", min_value=1, max_value=64000) 
  email = forms.CharField(label="Sending email", max_length=100)
  test_email = forms.CharField(label="Email for Test", max_length=100)
  
