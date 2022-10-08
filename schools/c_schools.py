from tools.djangodbasync import filterlinesdict
from .models import tag

def get_taglist(myschoolnr):
  count = 0
  taglist = list(tag.objects.filter(school = 1))
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
