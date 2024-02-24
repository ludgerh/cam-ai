import os
import base64
from cryptography.fernet import Fernet

class l_crypt(Fernet):

  def __init__(self, key=None, password=None):
    if key is None:
      if password is None:
        passbytes = os.urandom(32)
      else:
        passbytes = password.encode('utf-8')  
      multiplex = 32 // len(passbytes) + 1
      self.key = base64.urlsafe_b64encode((multiplex * passbytes)[:32])
    else:
      self.key = key  
    super().__init__(self.key)
