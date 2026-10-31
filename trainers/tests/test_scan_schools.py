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

# Level 2: job control of the trainer (scan_schools / insert_job) against the
# test database. The trainer is built but never started as a process, and
# redis is replaced by an in-memory fake, so a running server is not touched.

import asyncio
from logging import getLogger
from threading import Lock as t_lock
from unittest.mock import patch, AsyncMock
from asgiref.sync import sync_to_async
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from tools.c_redis import saferedis
from trainers.redis import redis as trainers_redis_class
from trainers.models import trainer as dbtrainer, trainframe, fit
from tf_workers.models import worker, school
from trainers import c_trainers
from trainers.c_trainers import trainer, SCHOOL_LOCK_KEY

class dict_redis_mixin():
  # Replaces the network calls of saferedis with a dict. Values are stored as
  # bytes like real redis returns them. TTLs are ignored.

  def __init__(self):
    self.store = {}

  def get(self, key):
    return(self.store.get(key))

  def set(self, key, value, ex = None, nx = False):
    if nx and key in self.store:
      return(None)
    if not isinstance(value, bytes):
      value = str(value).encode()
    self.store[key] = value
    return(True)

  def delete(self, key):
    return(1 if self.store.pop(key, None) is not None else 0)

class fake_trainers_redis(dict_redis_mixin, trainers_redis_class):
  pass

class fake_safe_redis(dict_redis_mixin, saferedis):
  pass

class ScanSchoolsTest(TestCase):

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
    self.trainer = self.make_trainer(self.dbtrainer)

  def make_trainer(self, dbline):
    # Same state async_runner() sets up, without process, tf_worker and logfile
    t = trainer(dbline.id, None, None, t_lock())
    t.dbline = dbline
    t.mylock = t_lock()
    t.job_queue = asyncio.Queue()
    t.job_queue_list = []
    t.school_cache = {}
    t.frames_cache = {}
    t.logname = 'trainer #' + str(dbline.id)
    t.logger = getLogger(t.logname)
    t.update_predictions = AsyncMock()
    self.trainers_redis.set_trainerqueue(dbline.id, [])
    return(t)

  def make_frames(self, myschool, count, checked = 1, train_status = 0):
    frames = [
      trainframe(
        made = timezone.now(),
        school = myschool.id,
        name = 'frame' + str(i) + '.bmp',
        code = 'NE',
        c0 = 1, c1 = 0, c2 = 0, c3 = 0, c4 = 0,
        c5 = 0, c6 = 0, c7 = 0, c8 = 0, c9 = 0,
        checked = checked,
        train_status = train_status,
      ) for i in range(count)
    ]
    trainframe.objects.bulk_create(frames)

  def queued_school_ids(self, t = None):
    t = t or self.trainer
    return([item[0].id for item in t.job_queue._queue])

  async def test_trigger_reached_inserts_job(self):
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 3)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [myschool.id])
    self.assertEqual(self.trainer.job_queue_list, [myschool.id])
    self.assertEqual(self.trainers_redis.get_trainerqueue(self.trainer.id), [myschool.id])
    self.assertEqual(
      await trainframe.objects.filter(school = myschool.id, train_status = 1).acount(), 3)
    myfit = await fit.objects.aget(school = myschool.id)
    self.assertEqual(myfit.status, 'Waiting')
    self.assertEqual(myfit.model_gamma, myschool.model_gamma)
    self.assertIsNone(self.safe_redis.get(SCHOOL_LOCK_KEY + str(myschool.id)))

  async def test_below_trigger_no_job(self):
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 2)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])
    self.assertFalse(await fit.objects.filter(school = myschool.id).aexists())
    self.assertEqual(
      await trainframe.objects.filter(school = myschool.id, train_status = 0).acount(), 2)

  async def test_second_scan_no_duplicate(self):
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 3)
    await self.trainer.scan_schools()
    # New frames arrive while the job is still queued
    await sync_to_async(self.make_frames)(myschool, 3)
    self.trainers_redis.set_last_frame(myschool.id, 42)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [myschool.id])
    self.assertEqual(await fit.objects.filter(school = myschool.id).acount(), 1)

  async def test_unchanged_school_is_skipped(self):
    myschool = await school.objects.acreate(**self.school_kwargs(trigger = 100))
    await self.trainer.scan_schools()
    # Trigger is lowered behind the cache's back: no school change and no
    # new frame -> the gate must skip the school.
    await sync_to_async(self.make_frames)(myschool, 3)
    self.trainer.school_cache[myschool.id]['trigger'] = 3
    await school.objects.filter(id = myschool.id).aupdate(trigger = 3)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])
    # A new last frame opens the gate
    self.trainers_redis.set_last_frame(myschool.id, 1)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [myschool.id])

  async def test_unchecked_frames_ignored(self):
    myschool = await school.objects.acreate(**self.school_kwargs(ignore_checked = False))
    await sync_to_async(self.make_frames)(myschool, 3, checked = 0)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])

  async def test_unchecked_frames_counted_with_ignore_checked(self):
    myschool = await school.objects.acreate(**self.school_kwargs(ignore_checked = True))
    await sync_to_async(self.make_frames)(myschool, 3, checked = 0)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [myschool.id])

  async def test_frames_in_training_not_counted(self):
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 3, train_status = 2)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])

  async def test_delegated_school_not_trained(self):
    myschool = await school.objects.acreate(**self.school_kwargs(delegation_level = 2))
    await sync_to_async(self.make_frames)(myschool, 3)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])
    # The migrations create a default school #1, so check only our school
    called_ids = [c.args[0] for c in self.trainer.update_predictions.call_args_list]
    self.assertNotIn(myschool.id, called_ids)

  async def test_inactive_school_ignored(self):
    myschool = await school.objects.acreate(**self.school_kwargs(active = 0))
    await sync_to_async(self.make_frames)(myschool, 3)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])

  async def test_trainer_request_below_trigger(self):
    myschool = await school.objects.acreate(**self.school_kwargs(trigger = 100))
    await sync_to_async(self.make_frames)(myschool, 1)
    await myschool.trainers.aadd(self.dbtrainer)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [myschool.id])
    self.assertFalse(await myschool.trainers.filter(id = self.dbtrainer.id).aexists())

  async def test_trainer_request_without_images(self):
    myschool = await school.objects.acreate(**self.school_kwargs())
    await myschool.trainers.aadd(self.dbtrainer)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])
    self.assertFalse(await myschool.trainers.filter(id = self.dbtrainer.id).aexists())

  async def test_queued_on_other_trainer(self):
    from globals.c_globals import trainers
    other_dbline = await dbtrainer.objects.acreate(name = 'Other Trainer')
    other = self.make_trainer(other_dbline)
    trainers[self.trainer.id] = self.trainer
    trainers[other.id] = other
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 3)
    await myschool.trainers.aadd(self.dbtrainer)
    self.trainers_redis.set_trainerqueue(other.id, [myschool.id])
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])
    self.assertFalse(await myschool.trainers.filter(id = self.dbtrainer.id).aexists())
    self.assertEqual(
      await trainframe.objects.filter(school = myschool.id, train_status = 0).acount(), 3)

  async def test_two_trainers_one_job(self):
    from globals.c_globals import trainers
    other_dbline = await dbtrainer.objects.acreate(name = 'Other Trainer')
    other = self.make_trainer(other_dbline)
    trainers[self.trainer.id] = self.trainer
    trainers[other.id] = other
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 3)
    await self.trainer.scan_schools()
    await other.scan_schools()
    self.assertEqual(self.queued_school_ids(), [myschool.id])
    self.assertEqual(self.queued_school_ids(other), [])
    self.assertEqual(await fit.objects.filter(school = myschool.id).acount(), 1)

  async def test_insert_job_respects_school_lock(self):
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 3)
    lock_key = SCHOOL_LOCK_KEY + str(myschool.id)
    self.safe_redis.set(lock_key, 99)
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])
    self.assertFalse(await fit.objects.filter(school = myschool.id).aexists())
    self.assertEqual(
      await trainframe.objects.filter(school = myschool.id, train_status = 0).acount(), 3)
    # The foreign lock must not be removed
    self.assertEqual(self.safe_redis.get(lock_key), b'99')

  async def test_got_sigint_stops_scan(self):
    myschool = await school.objects.acreate(**self.school_kwargs())
    await sync_to_async(self.make_frames)(myschool, 3)
    self.trainer.got_sigint = True
    await self.trainer.scan_schools()
    self.assertEqual(self.queued_school_ids(), [])

  def school_kwargs(self, **kwargs):
    result = {
      'name' : 'Test School',
      'creator' : self.user,
      'remote_creator' : self.user,
      'tf_worker' : self.worker,
      'trigger' : 3,
    }
    result.update(kwargs)
    return(result)
