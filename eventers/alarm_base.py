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

import json
from schools.c_schools import get_taglist

class alarm_base():
  def __init__(self, dbline, logger):
    self.params = json.loads(dbline.mendef)
    self.stream = dbline.mystream
    self.classes_list = get_taglist(dbline.mystream.eve_school.id)
    self.logger = logger
    
  def action(self, pred):
    mylist = list(pred)[1:]
    self.maxpos = mylist.index(max(mylist))  

