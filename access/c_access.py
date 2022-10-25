# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
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

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import access_control


@receiver(post_save, sender=access_control)
def create_user_api_key(sender, **kwargs):
  access.read_list()

class c_access():

  def __init__(self):
    self.read_list()

  def read_list(self):
    self.checklist = list(access_control.objects.all())

  def check(self, type, id, user, mode):
    if (user is None) or (user.id is None):
      userid = -1
    else:
      userid = user.id
    mychecklist = self.checklist
    mychecklist = [item for item in mychecklist if (item.vtype.upper()==type.upper() 
      or ((type.upper() in {'C','D','E'}) and (item.vtype.upper()=='X')) or item.vtype=='0')]
    mychecklist = [item for item in mychecklist if (item.vid==id or item.vid==0)]
    mychecklist = [item for item in mychecklist if ((item.u_g.upper()=='U') and (
      ((userid != -1) and ((item.u_g_nr==userid) or (item.u_g_nr==0) or (item.u_g_nr == -1)))
      or ((userid == -1) and (item.u_g_nr == -1))))]
    mychecklist = [item for item in mychecklist if (item.r_w.upper()==mode.upper() or item.r_w=='0' or item.r_w.upper()=='W')]
    if len(mychecklist) > 0:
      return(True)
    else:
      return(False)

  def filter_items(self, input, type, user, mode):
    output = []
    for item in input:
      if self.check(type, item.id, user, mode):
        output.append(item)
    return(output)

access = c_access()
