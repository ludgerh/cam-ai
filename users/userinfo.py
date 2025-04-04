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
from tools.health import totaldiscspace, useddiscspace
from .models import userinfo

def free_quota(myuser):
  if useddiscspace > totaldiscspace * 0.95:
    return(0)
  if myuser.is_superuser:
    if (diff := totaldiscspace - useddiscspace) > 0:
      return(diff)
    else:
      return(0)  
  else:
    try:
      userline = userinfo.objects.get(user = myuser)
    except userinfo.DoesNotExist:
      return(0) 
    if (diff := userline.storage_quota - userline.storage_used) > 0:
      return(diff)
    else:
      return(0)    

async def afree_quota(myuser):
  if useddiscspace > totaldiscspace * 0.95:
    return(0)
  if myuser.is_superuser:
    if (diff := totaldiscspace - useddiscspace) > 0:
      return(diff)
    else:
      return(0)  
  else:
    userline = await userinfo.objects.aget(user = myuser)
    if (diff := userline.storage_quota - userline.storage_used) > 0:
      return(diff)
    else:
      return(0)    
