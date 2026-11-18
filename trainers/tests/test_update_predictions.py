# trainers/tests/test_update_predictions.py
"""
Copyright (C) 2026 by the CAM-AI team, info@cam-ai.de
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

# Re-inferencing after a new fit (update_predictions) against the test
# database. tf_worker and redis are replaced by fakes, the frame files do not
# exist, so no image is ever sent for prediction.

from logging import getLogger
from threading import Lock as t_lock
from unittest.mock import patch, AsyncMock, MagicMock
from asgiref.sync import sync_to_async
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from trainers.models import trainer as dbtrainer, trainframe
from tf_workers.models import worker, school
from trainers import c_trainers
from trainers.c_trainers import trainer
from trainers.tests.test_scan_schools import fake_trainers_redis, fake_safe_redis

class UpdatePredictionsTest(TestCase):

  @classmethod
  def setUpTestData(cls):
    cls.user = User.objects.create(username = 'tester')
    cls.worker = worker.objects.create()
    cls.dbtrainer = dbtrainer.objects.create(name = 'Test Trainer')

  def setUp(self):
    self.trainers_redis = fake_trainers_redis()
    self.safe_redis = fake_safe_redis()
    for name, value in (
      ('trainers_redis', self.trainers_redis),
      ('safe_redis', self.safe_redis),
    ):
      p = patch.object(c_trainers, name, value)
      p.start()
      self.addCleanup(p.stop)
    p = patch.dict('globals.c_globals.trainers', clear = True)
    p.start()
    self.addCleanup(p.stop)
    t = trainer(self.dbtrainer.id, None, None, t_lock())
    t.dbline = self.dbtrainer
    t.mylock = t_lock()
    t.job_queue_list = []
    t.school_cache = {}
    t.frames_cache = {}
    t.logname = 'trainer #' + str(self.dbtrainer.id)
    t.logger = getLogger(t.logname)
    t.tf_worker = MagicMock()
    t.tf_worker.ask_pred = AsyncMock()
    t.tf_w_index = 7
    self.trainer = t

  def make_school(self, **kwargs):
    result = {
      'name' : 'Test School',
      'creator' : self.user,
      'remote_creator' : self.user,
      'tf_worker' : self.worker,
      'trigger' : 100000,
    }
    result.update(kwargs)
    return(school.objects.create(**result))

  def make_frames(self, myschool, count, last_fit = 0):
    trainframe.objects.bulk_create([
      trainframe(
        made = timezone.now(),
        school = myschool.id,
        name = 'frame' + str(i) + '.bmp',
        code = 'NE',
        c0 = 1, c1 = 0, c2 = 0, c3 = 0, c4 = 0,
        c5 = 0, c6 = 0, c7 = 0, c8 = 0, c9 = 0,
        checked = 1,
        last_fit = last_fit,
      ) for i in range(count)
    ])

  async def test_new_fit_requests_model_check(self):
    # The trainer raised last_fit, no tf_worker has loaded the model yet.
    myschool = await sync_to_async(self.make_school)(last_fit = 5, last_fit_infer = 4)
    await sync_to_async(self.make_frames)(myschool, 3, last_fit = 4)
    await self.trainer.update_predictions(myschool.id)
    self.trainer.tf_worker.ask_pred.assert_awaited_once_with(myschool.id, [], 7)
    self.assertEqual(self.trainer.doing_reinference, 0)
    self.assertFalse(self.trainers_redis.get_predict_proc_active(myschool.id))
    # The frames wait for the new model, they are not touched yet
    self.assertEqual(
      await trainframe.objects.filter(school = myschool.id, last_fit = 4).acount(), 3)

  async def test_current_model_nothing_to_do(self):
    myschool = await sync_to_async(self.make_school)(last_fit = 5, last_fit_infer = 5)
    await sync_to_async(self.make_frames)(myschool, 3, last_fit = 5)
    await self.trainer.update_predictions(myschool.id)
    self.trainer.tf_worker.ask_pred.assert_not_awaited()
    self.assertEqual(self.trainer.doing_reinference, 0)

  async def test_exception_releases_reservation(self):
    with self.assertRaises(school.DoesNotExist):
      await self.trainer.update_predictions(999999)
    self.assertEqual(self.trainer.doing_reinference, 0)
    self.assertFalse(self.trainers_redis.get_predict_proc_active(999999))

  async def test_partial_run_keeps_reservation(self):
    # More frames than one pass handles (1000): the school stays reserved.
    myschool = await sync_to_async(self.make_school)(last_fit = 5, last_fit_infer = 5)
    await sync_to_async(self.make_frames)(myschool, 1001, last_fit = 4)
    await self.trainer.update_predictions(myschool.id)
    self.assertEqual(self.trainer.doing_reinference, myschool.id)
    self.assertFalse(self.trainers_redis.get_predict_proc_active(myschool.id))
    # Another school has to wait
    other = await sync_to_async(self.make_school)(last_fit = 2, last_fit_infer = 1)
    await self.trainer.update_predictions(other.id)
    self.trainer.tf_worker.ask_pred.assert_not_awaited()

  async def test_busy_school_does_not_reserve(self):
    # Another trainer is re-inferencing the school right now.
    myschool = await sync_to_async(self.make_school)(last_fit = 5, last_fit_infer = 4)
    self.trainers_redis.set_predict_proc_active(myschool.id, True)
    await self.trainer.update_predictions(myschool.id)
    self.assertEqual(self.trainer.doing_reinference, 0)
    self.trainer.tf_worker.ask_pred.assert_not_awaited()

  async def test_scan_reaches_every_school(self):
    # Regression: with one task per school, every second school lost the race
    # for doing_reinference on each pass and never got its model checked.
    myschools = []
    for i in range(6):
      myschools.append(
        await sync_to_async(self.make_school)(last_fit = 2, last_fit_infer = 1))
    await self.trainer.scan_schools()
    await self.trainer.reinference_task
    asked = [c.args[0] for c in self.trainer.tf_worker.ask_pred.await_args_list]
    for myschool in myschools:
      self.assertIn(myschool.id, asked)

  async def test_reserved_school_first_and_alone(self):
    self.trainer.update_predictions = AsyncMock()
    self.trainer.doing_reinference = 3
    await self.trainer.run_reinference([1, 2, 3])
    # A partly done school stays reserved, nothing else runs in this pass
    self.trainer.update_predictions.assert_awaited_once_with(3)

  async def test_failing_school_does_not_stop_others(self):
    self.trainer.update_predictions = AsyncMock(side_effect = [ValueError, None])
    with self.assertLogs(self.trainer.logger, 'ERROR'):
      await self.trainer.run_reinference([1, 2])
    self.assertEqual(
      [c.args[0] for c in self.trainer.update_predictions.await_args_list], [1, 2])

  async def test_scan_releases_deactivated_school(self):
    self.trainer.update_predictions = AsyncMock()
    myschool = await sync_to_async(self.make_school)()
    self.trainer.doing_reinference = myschool.id
    await self.trainer.scan_schools()
    self.assertEqual(self.trainer.doing_reinference, myschool.id)
    await school.objects.filter(id = myschool.id).aupdate(active = False)
    await self.trainer.scan_schools()
    self.assertEqual(self.trainer.doing_reinference, 0)

  async def test_scan_keeps_running_reservation(self):
    self.trainer.update_predictions = AsyncMock()
    myschool = await sync_to_async(self.make_school)(active = False)
    self.trainer.doing_reinference = myschool.id
    self.trainers_redis.set_predict_proc_active(myschool.id, True)
    await self.trainer.scan_schools()
    self.assertEqual(self.trainer.doing_reinference, myschool.id)
