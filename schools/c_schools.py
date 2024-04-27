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

from tools.djangodbasync import filterlinesdict
from django.db import connection
from django.db.utils import OperationalError
from .models import tag

def get_taglist(myschoolnr):
  count = 0
  while True:
    try:
      taglist = list(tag.objects.filter(school = 1))
      break
    except OperationalError:
      connection.close()
  for item in taglist:
    item.id = count
    count += 1
  if myschoolnr > 1:
    extralist = tag.objects.filter(school = myschoolnr)
    for item in extralist:
      taglist[item.replaces].name = item.name 
      taglist[item.replaces].description = item.description
  return(taglist)

def get_tagnamelist(myschoolnr):
  result = []
  for item in get_taglist(myschoolnr):
    result.append(item.name)
  return(result)

def check_extratags(myschoolnr, mytrainframe):
  extralist = tag.objects.filter(school = myschoolnr)
  for item in extralist:
    for i in range(10):
      if ((item.replaces == i) and mytrainframe['c'+str(i)]):
        return(True)
  return(False)

async def check_extratags_async(myschoolnr, mytrainframe):
  extralist = await filterlinesdict(tag, {'school' : myschoolnr, }, ['replaces'])
  for item in extralist:
    for i in range(10):
      if ((item['replaces'] == i) and mytrainframe['c'+str(i)]):
        return(True)
  return(False)
