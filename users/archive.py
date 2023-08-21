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

from os import path, makedirs, remove
from shutil import copy
from tools.l_tools import djconf, uniquename
from eventers.models import event, event_frame
from users.models import archive as dbarchive
from access.c_access import access

class archive():
  def __init__(self):
    self.archivepath = djconf.getconfig('archivepath', 'data/archive/')
    if not path.exists(self.archivepath+'frames/'):
      makedirs(self.archivepath+'frames/')
    if not path.exists(self.archivepath+'videos/'):
      makedirs(self.archivepath+'videos/')

  def to_archive(self, mytype, mynumber, user):
    if mytype == 0:
      frameline = event_frame.objects.get(id=mynumber)
      if access.check('S', frameline.event.school.id, user, 'W'):
        if frameline.hasarchive:
          archiveline = dbarchive.objects.get(typecode=0, number = mynumber)
        else:
          sourcedir = djconf.getconfig('schoolframespath', 'data/schoolframes/')
          targetdir = self.archivepath + 'frames/'
          targetname = frameline.name.split('/')[-1]
          targetname = uniquename(targetdir, targetname.split('.')[0], targetname.split('.')[1])
          copy(sourcedir+frameline.name, targetdir+targetname)
          archiveline = dbarchive(
            typecode=0, 
            number=frameline.id, 
            school=frameline.event.school, 
            name=targetname, 
            made=frameline.time,
          )
          archiveline.save()
          frameline.hasarchive = True
          frameline.save(update_fields=["hasarchive"])
        archiveline.users.add(user)
        archiveline.save()
    elif mytype == 1:
      eventline = event.objects.get(id=mynumber)
      if access.check('S', eventline.school.id, user, 'W'):
        if eventline.hasarchive:
          archiveline = dbarchive.objects.get(typecode=1, number = mynumber)
        else:
          sourcedir = djconf.getconfig('recordingspath', 'data/recordings/')
          sourcename1 = eventline.videoclip + '.mp4'
          sourcename2 = eventline.videoclip + '.jpg'
          sourcename3 = eventline.videoclip + '.webm'
          targetdir = self.archivepath + 'videos/'
          targetname1 = uniquename(targetdir, eventline.videoclip, 'mp4')
          targetname = targetname1.split('.')[0]
          targetname2 = targetname + '.jpg'
          targetname3 = targetname + '.webm'
          if path.exists(sourcedir+sourcename1):
            copy(sourcedir+sourcename1, targetdir+targetname1)
          if path.exists(sourcedir+sourcename2):
            copy(sourcedir+sourcename2, targetdir+targetname2)
          if path.exists(sourcedir+sourcename3):
            copy(sourcedir+sourcename3, targetdir+targetname3)
          archiveline = dbarchive(
            typecode=1, 
            number=eventline.id, 
            school=eventline.school, 
            name=targetname, 
            made=eventline.start,
          )
          archiveline.save()
          eventline.hasarchive = True
          eventline.save(update_fields=["hasarchive"])
        archiveline.users.add(user)
        archiveline.save()

  def check_archive(self, mytype, mynumber, user):
    try:
      archiveline = dbarchive.objects.get(typecode=mytype, number = mynumber)
    except dbarchive.DoesNotExist:
      return(False)
    return(len(archiveline.users.filter(id=user)) > 0)
    
  def del_archive(self, line_nr, user):
    archiveline = dbarchive.objects.get(id = line_nr)
    if access.check('S', archiveline.school.id, user, 'W'):
      archiveline.users.remove(user)
      if len(archiveline.users.all()) == 0:
        if archiveline.typecode == 0:
          try:
            frameline = event_frame.objects.get(id=archiveline.number)
            frameline.hasarchive = False
            frameline.save(update_fields=["hasarchive"])
          except event_frame.DoesNotExist:
            pass
          targetdir = self.archivepath + 'frames/'
          if path.exists(targetdir+archiveline.name):
            remove(targetdir+archiveline.name)
        elif archiveline.typecode == 1:
          try:
            eventline = event.objects.get(id=archiveline.number)
            eventline.hasarchive = False
            eventline.save(update_fields=["hasarchive"])
          except event.DoesNotExist:
            pass
          targetdir = self.archivepath + 'videos/'
          targetname = archiveline.name + '.mp4'
          if path.exists(targetdir+targetname):
            remove(targetdir+targetname)
          targetname = archiveline.name + '.jpg'
          if path.exists(targetdir+targetname):
            remove(targetdir+targetname)
          targetname = archiveline.name + '.webm'
          if path.exists(targetdir+targetname):
            remove(targetdir+targetname)
        archiveline.delete()
    

myarchive = archive()
