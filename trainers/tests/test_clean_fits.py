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

# clean_fits(): resets unfinished fits and removes stale temp models.

import os
import tempfile
from shutil import rmtree
from asgiref.sync import async_to_sync
from django.test import TestCase
from django.contrib.auth.models import User
from tf_workers.models import worker, school
from trainers.models import fit
from trainers.c_trainers import clean_fits

MODEL = 'efficientnetv2-b0'

class CleanFitsTest(TestCase):

  def setUp(self):
    self.tmpdir = tempfile.mkdtemp(prefix = 'camai_clean_test_')
    self.addCleanup(rmtree, self.tmpdir, True)
    self.user = User.objects.create(username = 'tester')
    self.worker = worker.objects.create()
    # Schools from the migrations point to the live data/schools/ dirs
    school.objects.update(dir = os.path.join(self.tmpdir, 'migrated') + '/')

  def make_school(self, name, files = ()):
    school_dir = os.path.join(self.tmpdir, name) + '/'
    os.makedirs(school_dir + 'model/')
    for filename in files:
      with open(school_dir + 'model/' + filename, 'wb') as f:
        f.write(b'x')
    school.objects.create(
      name = name,
      dir = school_dir,
      creator = self.user,
      remote_creator = self.user,
      tf_worker = self.worker,
    )
    return(school_dir)

  async def test_unfinished_fits_stopped(self):
    for status in ('Waiting', 'Queuing', 'Working', 'Done', 'Stopped', 'NoQuota'):
      await fit.objects.acreate(school = 1, status = status)
    await clean_fits()
    result = sorted([item async for item in fit.objects.values_list('status', flat = True)])
    self.assertEqual(result, sorted(
      ['Stopped', 'Stopped', 'Stopped', 'Done', 'Stopped', 'NoQuota']))

  def test_temp_models_removed(self):
    keep = [MODEL + '.keras', MODEL + '.tflite', 'q_' + MODEL + '.tflite',
      MODEL + '_12.keras']   # backup copy (schools_backup), not a temp file
    dir1 = self.make_school('s1', keep + [MODEL + '_temp_5.keras', MODEL + '_temp_216.keras'])
    dir2 = self.make_school('s2', ['efficientnetv2-b3_temp_7.keras'])
    removed = async_to_sync(clean_fits)()
    self.assertEqual(sorted(removed), sorted([
      dir1 + 'model/' + MODEL + '_temp_5.keras',
      dir1 + 'model/' + MODEL + '_temp_216.keras',
      dir2 + 'model/efficientnetv2-b3_temp_7.keras',
    ]))
    self.assertEqual(sorted(os.listdir(dir1 + 'model/')), sorted(keep))
    self.assertEqual(os.listdir(dir2 + 'model/'), [])

  def test_missing_dir_and_shared_dir(self):
    shared = self.make_school('shared', [MODEL + '_temp_1.keras'])
    school.objects.create(name = 'same dir', dir = shared, creator = self.user,
      remote_creator = self.user, tf_worker = self.worker)
    school.objects.create(name = 'no dir', dir = self.tmpdir + '/missing/',
      creator = self.user, remote_creator = self.user, tf_worker = self.worker)
    removed = async_to_sync(clean_fits)()
    self.assertEqual(removed, [shared + 'model/' + MODEL + '_temp_1.keras'])
