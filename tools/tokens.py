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

