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

from itertools import chain
from channels.db import database_sync_to_async

def model_to_dict(dbline, fields=None):
  opts = dbline._meta
  data = {}
  for f in chain(opts.concrete_fields, opts.private_fields):
    if (fields is None) or (f.name in fields):
      data[f.name] = f.value_from_object(dbline)
  for f in opts.many_to_many:
    if (fields is None) or (f.name in fields):
      data[f.name] = [i.id for i in f.value_from_object(dbline)]
  return data

@database_sync_to_async
def savedbline(dbline, fields=None):
  #print(dbline, fields)
  if fields is None:
    dbline.save()
  else:
    dbline.save(update_fields=fields)
  return(dbline.id)

@database_sync_to_async
def deldbline(dbline):
  dbline.delete()

@database_sync_to_async
def deletefilter(model, filterdict):
  model.objects.filter(**filterdict).delete()

@database_sync_to_async
def updatefilter(model, filterdict, changedict):
  model.objects.filter(**filterdict).update(**changedict)

@database_sync_to_async
def getoneline(model, filterdict):
  return(model.objects.get(**filterdict))

@database_sync_to_async
def getonelinedict(model, filterdict, fields=None):
  result = model.objects.get(**filterdict)
  return(model_to_dict(result, fields=fields))

@database_sync_to_async
def filterlines(model, filterdict):
  return(model.objects.filter(**filterdict).order_by("id"))

@database_sync_to_async
def filterlinesdict(model, filterdict=None, fields=None):
  if filterdict is None:
    alllines = model.objects.all().order_by("id")
  else:
    alllines = model.objects.filter(**filterdict).order_by("id")
  return([model_to_dict(item, fields=fields) for item in alllines])

@database_sync_to_async
def countfilter(model, filterdict):
  return(model.objects.filter(**filterdict).count())

