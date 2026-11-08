# schools/tests.py
"""
Copyright (C) 2024-2026 by the CAM-AI team, info@cam-ai.de
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
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from django.test import SimpleTestCase
from schools.c_schools import frame_path

class frame_path_test(SimpleTestCase):

  def setUp(self):
    self.tempdir = TemporaryDirectory()
    self.schoolline = SimpleNamespace(
      dir = self.tempdir.name + '/',
      model_xin = 300,
      model_yin = 200,
    )

  def tearDown(self):
    self.tempdir.cleanup()

  def make_file(self, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok = True)
    with open(filepath, 'wb') as f:
      f.write(b'x')

  def test_original_frame(self):
    framepath = self.schoolline.dir + 'frames/sub/img.bmp'
    self.make_file(framepath)
    self.make_file(self.schoolline.dir + 'coded/300x200/sub/img.cod')
    self.assertEqual(frame_path(self.schoolline, 'sub/img.bmp'), framepath)

  def test_coded_only(self):
    # Coded copy is taken from the directory of the model input size
    self.assertEqual(
      frame_path(self.schoolline, 'sub/img.bmp'),
      self.schoolline.dir + 'coded/300x200/sub/img.cod',
    )
