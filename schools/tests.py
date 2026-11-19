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
import numpy as np
import cv2 as cv
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from asgiref.sync import async_to_sync
from django.test import SimpleTestCase
from schools.c_schools import frame_path
from schools import consumers
from trainers.models import trainframe

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


class fake_tf_worker():

  def __init__(self, answer = True):
    self.answer = answer
    self.out = None

  async def ask_pred(self, school, image_list, tf_w_index):
    if self.answer and image_list:
      self.out = np.full((len(image_list), 10), 0.75)

  async def outqueue_empty(self, userindex):
    return(self.out is None)

  async def get_from_outqueue(self, userindex, timeout = None):
    result = self.out
    self.out = None
    return(result)


class predictions_from_tfw_test(SimpleTestCase):

  def setUp(self):
    self.tempdir = TemporaryDirectory()
    self.schoolline = SimpleNamespace(last_fit = 7)
    consumers.schooldbutil.school_lines[999] = self.schoolline
    consumers.schooldbutil.cache_dict['school'].clear()
    good = np.zeros((20, 20, 3), dtype = np.uint8)
    cv.imwrite(self.tempdir.name + '/good.jpg', good)
    with open(self.tempdir.name + '/bad.jpg', 'wb') as f:
      f.write(b'no image')
    self.names = {1 : 'good.jpg', 2 : 'bad.jpg', 3 : 'missing.jpg'}

  def tearDown(self):
    consumers.schooldbutil.school_lines.pop(999, None)
    consumers.schooldbutil.cache_dict['school'].clear()
    self.tempdir.cleanup()

  async def fake_aget(self, id):
    if id not in self.names:
      raise trainframe.DoesNotExist()
    return(SimpleNamespace(id = id, name = self.names[id], last_fit = 0))

  def run_predictions(self, tf_worker, idx_list):
    consumer = consumers.schooldbutil()
    consumer.tf_worker = tf_worker
    consumer.tf_w_index = 0
    frames = [{'idx' : idx} for idx in idx_list]
    with (
      patch.object(trainframe.objects, 'aget', self.fake_aget),
      patch.object(consumers, 'frame_path',
        lambda school, name: self.tempdir.name + '/' + name),
      patch.object(consumers, 'PRED_TIMEOUT', 0.01),
    ):
      async_to_sync(consumer.predictions_from_tfw)(frames, 999, False)
    return({item['idx'] : item['prediction'] for item in frames})

  def test_unreadable_frames(self):
    # Corrupt, missing and deleted frames get None, the others a prediction
    result = self.run_predictions(fake_tf_worker(), [2, 1, 3, 4])
    self.assertEqual(result[1], [0.75] * 10)
    self.assertIsNone(result[2])
    self.assertIsNone(result[3])
    self.assertIsNone(result[4])

  def test_worker_no_answer(self):
    # The request returns without predictions instead of waiting forever
    result = self.run_predictions(fake_tf_worker(answer = False), [1])
    self.assertIsNone(result[1])
