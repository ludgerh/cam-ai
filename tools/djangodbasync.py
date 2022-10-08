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

