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

from string import ascii_letters
from random import choice
from datetime import datetime
from time import time
from django.utils import timezone
from .models import token

def maketoken(cat, idx, info='...'):
  password = ''.join(choice(ascii_letters) for i in range(20))
  mytoken = token(
    passwd = password,
    made = timezone.make_aware(datetime.fromtimestamp(time())),
    cat = cat,
    idx = idx,
    info = info,
  )
  mytoken.save()
  result = (mytoken.id, password)
  return(result)

async def maketoken_async(cat, idx, info='...'):
  password = ''.join(choice(ascii_letters) for i in range(20))
  mytoken = token(
    passwd = password,
    made = timezone.make_aware(datetime.fromtimestamp(time())),
    cat = cat,
    idx = idx,
    info = info,
  )
  await mytoken.asave()
  result = (mytoken.id, password)
  return(result)

def checktoken(mytoken, cat=None, idx=None, timeout=None, maxcount=None):
  try:
    tokenline = token.objects.get(id = mytoken[0])
  except token.DoesNotExist:
    return(False)
  if not tokenline.valid:
    return(False)
  elif tokenline.passwd != mytoken[1]:
    return(False)
  elif cat and tokenline.cat != cat:
    return(False)
  elif idx and tokenline.idx != idx:
    return(False)
  elif timeout and ((timezone.now() - tokenline.made).total_seconds() > timeout):
    return(False)
  elif maxcount and (tokenline.count >= maxcount):
    return(False)
  tokenline.count += 1
  tokenline.save(update_fields = ['count', ])
  return(True)

