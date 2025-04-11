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
