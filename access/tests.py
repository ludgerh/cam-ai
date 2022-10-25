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

from django.test import TestCase
from .c_access import access
from .models import access_control

class userclass():

  def __init__(self, idx):
    self.id = idx

class accesstest(TestCase):

  def test_empty_list(self):
    """
    Several tests with empty list
    """
    access.read_list()
    for i in range(1, 20):
      user = userclass(i)
      for type in ('c', 'd', 'e', 'x', 'C', 'D', 'E', 'X'):
        for nr in range(1, 20):
          for mode in ('r', 'R', 'w', 'W', '0'):
            self.assertIs(access.check(type, nr, user, mode), False)

  def test_all_allowed(self):
    """
    Several tests with one line: Everything allowed
    """
    newline = access_control(vtype=0, vid=0, u_g='U', u_g_nr=0, r_w=0)
    newline.save()
    access.read_list()
    for i in range(1, 20):
      user = userclass(i)
      for type in ('c', 'd', 'e', 'x', 'C', 'D', 'E', 'X'):
        for nr in range(1, 20):
          for mode in ('r', 'R', 'w', 'W', '0'):
            self.assertIs(access.check(type, nr, user, mode), True)
    """
    Adding one specific line
    """
    newline = access_control(vtype='C', vid=1, u_g='U', u_g_nr=1, r_w='r')
    newline.save()
    access.read_list()
    for i in range(1, 20):
      user = userclass(i)
      for type in ('c', 'd', 'e', 'x', 'C', 'D', 'E', 'X'):
        for nr in range(1, 20):
          for mode in ('r', 'R', 'w', 'W', '0'):
            self.assertIs(access.check(type, nr, user, mode), True)

  def test_check_specific_1(self):
    """
    More specific tests #1
    """
    newline = access_control(vtype='C', vid=13, u_g='U', u_g_nr=13, r_w='r')
    newline.save()
    access.read_list()
    user = userclass(13)
    self.assertIs(access.check('C', 13, user, 'r'), True)
    self.assertIs(access.check('C', 13, user, 'R'), True)
    self.assertIs(access.check('C', 13, user, 'w'), False)
    self.assertIs(access.check('C', 13, user, 'W'), False)
    self.assertIs(access.check('C', 13, user, '0'), False)

  def test_check_specific_2(self):
    """
    More specific tests #2
    """

    newline = access_control(vtype='X', vid=13, u_g='U', u_g_nr=13, r_w='r')
    newline.save()
    access.read_list()
    user = userclass(13)
    self.assertIs(access.check('C', 13, user, 'r'), True)
    self.assertIs(access.check('C', 13, user, 'R'), True)
    self.assertIs(access.check('C', 13, user, 'w'), False)
    self.assertIs(access.check('C', 13, user, 'W'), False)
    self.assertIs(access.check('C', 13, user, '0'), False)

  def test_check_specific_3(self):
    """
    More specific tests #3
    """

    newline = access_control(vtype='C', vid=13, u_g='U', u_g_nr=13, r_w='w')
    newline.save()
    access.read_list()
    user = userclass(13)
    self.assertIs(access.check('C', 13, user, 'r'), True)
    self.assertIs(access.check('C', 13, user, 'R'), True)
    self.assertIs(access.check('C', 13, user, 'w'), True)
    self.assertIs(access.check('C', 13, user, 'W'), True)
    self.assertIs(access.check('C', 13, user, '0'), True)

  def test_check_specific_4(self):
    """
    More specific tests #4
    """

    newline = access_control(vtype='X', vid=13, u_g='U', u_g_nr=13, r_w='w')
    newline.save()
    access.read_list()
    user = userclass(13)
    self.assertIs(access.check('C', 13, user, 'r'), True)
    self.assertIs(access.check('C', 13, user, 'R'), True)
    self.assertIs(access.check('C', 13, user, 'w'), True)
    self.assertIs(access.check('C', 13, user, 'W'), True)
    self.assertIs(access.check('C', 13, user, '0'), True)

  def test_check_specific_5(self):
    """
    More specific tests #5
    """

    newline = access_control(vtype='C', vid=13, u_g='U', u_g_nr=13, r_w='w')
    newline.save()
    access.read_list()
    user = userclass(13)
    self.assertIs(access.check('D', 13, user, 'r'), False)
    self.assertIs(access.check('D', 13, user, 'R'), False)
    self.assertIs(access.check('D', 13, user, 'w'), False)
    self.assertIs(access.check('D', 13, user, 'W'), False)
    self.assertIs(access.check('D', 13, user, '0'), False)

  def test_check_specific_6(self):
    """
    More specific tests #6
    """

    newline = access_control(vtype='C', vid=13, u_g='U', u_g_nr=13, r_w='w')
    newline.save()
    access.read_list()
    user = userclass(13)
    self.assertIs(access.check('c', 13, user, 'r'), True)
    self.assertIs(access.check('c', 13, user, 'R'), True)
    self.assertIs(access.check('c', 13, user, 'w'), True)
    self.assertIs(access.check('c', 13, user, 'W'), True)
    self.assertIs(access.check('c', 13, user, '0'), True)

  def test_check_specific_7(self):
    """
    More specific tests #7
    """

    newline = access_control(vtype='C', vid=13, u_g='U', u_g_nr=13, r_w='w')
    newline.save()
    access.read_list()
    user = userclass(13)
    self.assertIs(access.check('c', 12, user, 'r'), False)
    self.assertIs(access.check('c', 12, user, 'R'), False)
    self.assertIs(access.check('c', 12, user, 'w'), False)
    self.assertIs(access.check('c', 12, user, 'W'), False)
    self.assertIs(access.check('c', 12, user, '0'), False)

  def test_check_specific_8(self):
    """
    More specific tests #8
    """

    newline = access_control(vtype='C', vid=13, u_g='U', u_g_nr=13, r_w='w')
    newline.save()
    access.read_list()
    user = userclass(12)
    self.assertIs(access.check('c', 13, user, 'r'), False)
    self.assertIs(access.check('c', 13, user, 'R'), False)
    self.assertIs(access.check('c', 13, user, 'w'), False)
    self.assertIs(access.check('c', 13, user, 'W'), False)
    self.assertIs(access.check('c', 13, user, '0'), False)

