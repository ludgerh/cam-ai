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
from .l_buffer import l_buffer
from time import sleep
from multiprocessing import Process
import numpy as np


mydata = (1, 2, 3, 'ABC', [1, 2, 3], {'abc':1, 'def':2, 'ghi':3}, np.arange(9).reshape(3, 3))

class l_buffer_test(TestCase):

  def test_a1false(self):
    """
    Single Thread, No Buffer, No Block, No Callback
    """
    mybuffer = l_buffer('A', 1)
    for item in mydata:
      mybuffer.put(item)
      if type(item) == np.ndarray:
        self.assertIs(np.all(mybuffer.get()), np.all(item))
      else:
        self.assertIs(mybuffer.get(), item)

  def test_a1true(self):
    """
    Single Thread, No Buffer, No Block, Callback
    """
    def mycallback():
      self.callback_worked = True
    mybuffer = l_buffer('A', 1, mycallback)
    for item in mydata:
      self.callback_worked = False 
      mybuffer.put(item)
      if type(item) == np.ndarray:
        self.assertIs(np.all(mybuffer.get()), np.all(item))
      else:
        self.assertIs(mybuffer.get(), item)
      self.assertIs(self.callback_worked, True)

  def test_d1false(self):
    """
    Single Thread, No Buffer, No Block, No Callback
    """
    mybuffer = l_buffer('D', 1)
    for item in mydata:
      mybuffer.put(item)
      self.assertIs(np.all(mybuffer.get() == item).item(0), True)
    mybuffer.stop()

  def test_d1true(self):
    """
    Single Thread, No Buffer, No Block, Callback
    """
    def worker():
      sleep(0.1)
      self.mybuffer.put(item)
    def mycallback():
      self.callback_worked = True
    self.mybuffer = l_buffer('D', 1, mycallback)
    for item in mydata:
      self.callback_worked = False 
      myprocess = Process(target = worker)
      myprocess.start()
      sleep(0.2)
      self.assertIs(np.all(self.mybuffer.get() == item).item(0), True)
      self.assertIs(self.callback_worked, True)
      myprocess.kill()
    self.mybuffer.stop()

  def test_d2false(self):
    """
    Single Thread, No Buffer, No Block, No Callback
    """
    mybuffer = l_buffer('D', 2)
    for item in mydata:
      mybuffer.put(item)
      self.assertIs(np.all(mybuffer.get() == item).item(0), True)
    mybuffer.stop()

  def test_d2true(self):
    """
    Single Thread, No Buffer, No Block, Callback
    """
    def worker():
      sleep(0.1)
      self.mybuffer.put(item)
    def mycallback():
      self.callback_worked = True
    self.mybuffer = l_buffer('D', 2, mycallback)
    for item in mydata:
      self.callback_worked = False 
      myprocess = Process(target = worker)
      myprocess.start()
      sleep(0.2)
      self.assertIs(np.all(self.mybuffer.get() == item).item(0), True)
      self.assertIs(self.callback_worked, True)
      myprocess.kill()
    self.mybuffer.stop()
