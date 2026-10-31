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

# Level 3: a real training run with a school exported from the live system.
#
#   python manage.py export_school 8 --frames 200
#   python manage.py test trainers --tag slow
#
# The export is loaded into the test DB and its files are copied to a temp
# directory, so neither the live DB nor data/schools/ is touched. Runs on the
# CPU, with a frozen base model and few epochs to keep it at a few minutes.
#
# Environment: CAMAI_TEST_SCHOOL (export dir), CAMAI_TEST_EPOCHS

import json
import os
import tempfile
from math import isfinite
from shutil import copytree, rmtree
from unittest import skipIf
from unittest.mock import patch
from django.test import TransactionTestCase, tag as test_tag
from django.utils.dateparse import parse_datetime
from django.contrib.auth.models import User
from tf_workers.models import worker, school
from trainers.models import trainframe, fit, epoch
from schools.models import tag

try:
  from plugins.train_worker_gpu import train_worker_gpu
  plugin_missing = False
except ImportError:
  plugin_missing = True

EXPORT_DIR = os.environ.get('CAMAI_TEST_SCHOOL', 'temp/test_schools/school8/')
EPOCHS = int(os.environ.get('CAMAI_TEST_EPOCHS', 6))
GPU_NR = -1  # CPU only

class fake_djconf():
  # Config values for the training process. Replaces the DB-backed djconf of
  # the plugin so the live settings (e.g. tr_epochs) do not leak in.

  def __init__(self, values):
    self.values = values

  def getconfig(self, param, default = None, forcedb = False):
    return(self.values.get(param, default))

  getconfigint = getconfig
  getconfigfloat = getconfig
  getconfigbool = getconfig

@test_tag('slow')
@skipIf(plugin_missing, 'plugins/train_worker_gpu not installed')
@skipIf(not os.path.exists(EXPORT_DIR + 'school.json'),
  'No school export, run: python manage.py export_school 8 --frames 200')
class TrainSchoolTest(TransactionTestCase):
  # TransactionTestCase, because the trainer closes the DB connection
  # (get_taglist(), before model.fit()), which would break the transaction
  # of a normal TestCase.

  def setUp(self):
    with open(EXPORT_DIR + 'school.json') as f:
      self.export = json.load(f)
    self.tmpdir = tempfile.mkdtemp(prefix = 'camai_train_test_')
    self.addCleanup(rmtree, self.tmpdir, True)
    self.school_dir = self.tmpdir + '/school/'
    copytree(EXPORT_DIR, self.school_dir)
    self.user = User.objects.create(username = 'tester')
    self.worker = worker.objects.create()

    school_row = dict(self.export['school'])
    school_row['lastmodelfile'] = parse_datetime(school_row['lastmodelfile'])
    # Single stage with frozen base model: tests the whole pipeline without
    # the hours a full finetuning run takes.
    school_row['model_finetuning'] = 0
    school_row['save_new_model'] = True
    self.myschool = school.objects.create(
      creator = self.user,
      remote_creator = self.user,
      tf_worker = self.worker,
      dir = self.school_dir,
      **school_row,
    )

    # Tags: replace the migration defaults by the exported ones
    tag.objects.all().delete()
    for row in self.export['tags']:
      if row['school'] != 1:
        row['school'] = self.myschool.id
      tag.objects.create(**row)

    frames = []
    for row in self.export['frames']:
      row = dict(row)
      row['made'] = parse_datetime(row['made'])
      frames.append(trainframe(school = self.myschool.id, **row))
    trainframe.objects.bulk_create(frames)

    # As insert_job() does it
    self.myfit = fit.objects.create(
      school = self.myschool.id,
      model_image_augmentation = self.myschool.model_image_augmentation,
      model_gamma = self.myschool.model_gamma,
      model_gamma_step = self.myschool.model_gamma_step,
      model_gamma_max = self.myschool.model_gamma_max,
      model_finetuning = self.myschool.model_finetuning,
      status = 'Waiting',
    )

    datapath = self.tmpdir + '/data/'
    config = {
      'version' : train_worker_gpu.version,
      'tr_epochs' : EPOCHS,
      'tr_batchsize' : 32,
      'validation_split' : 0.33333333,
      'schools_backup' : False,
      'datapath' : datapath,
      'schools_dir' : datapath + 'schools/',
    }
    for target, value in (
      ('plugins.train_worker_gpu.train_worker_gpu.djconf', fake_djconf(config)),
      # Quota needs the disk usage from the live redis
      ('users.userinfo.free_quota', lambda myuser: 1),
    ):
      p = patch(target, value)
      p.start()
      self.addCleanup(p.stop)

  def test_train_school(self):
    model_name = self.myschool.model_train_type
    modelpath = self.school_dir + 'model/'
    nr_frames = len(self.export['frames'])
    # train_once_gpu() changes myschool in place, so read it before
    old_last_fit = self.myschool.last_fit

    train_worker_gpu.train_once_gpu(self.myschool, self.myfit, GPU_NR, 0)

    # --- fit -------------------------------------------------------------------
    self.myfit.refresh_from_db()
    self.assertEqual(self.myfit.status, 'Done')
    self.assertEqual(self.myfit.nr_tr + self.myfit.nr_va, nr_frames)
    self.assertGreater(self.myfit.nr_va, 0)
    self.assertGreaterEqual(self.myfit.epochs, 1)
    self.assertLessEqual(self.myfit.epochs, EPOCHS)
    for field in ('loss', 'bce', 'val_loss', 'val_bce'):
      value = getattr(self.myfit, field)
      self.assertTrue(isfinite(value), field + ' = ' + str(value))
      self.assertGreater(value, 0.0, field)
    for field in ('binacc', 'val_binacc', 'recall', 'precision',
        'val_recall', 'val_precision'):
      value = getattr(self.myfit, field)
      self.assertTrue(0.0 <= value <= 1.0, field + ' = ' + str(value))
    self.assertIsNotNone(self.myfit.val_errors)
    self.assertLessEqual(self.myfit.val_errors, self.myfit.nr_va)

    # --- epochs ----------------------------------------------------------------
    epochs = list(epoch.objects.filter(fit = self.myfit).order_by('id'))
    self.assertGreaterEqual(len(epochs), self.myfit.epochs)
    self.assertLessEqual(len(epochs), EPOCHS)
    for item in epochs:
      self.assertTrue(isfinite(item.loss) and isfinite(item.val_loss))
      self.assertGreater(item.seconds, 0.0)

    # --- frames ----------------------------------------------------------------
    self.assertFalse(trainframe.objects.filter(
      school = self.myschool.id, code = 'NE').exists())

    # --- model files -----------------------------------------------------------
    for filename in (model_name + '.keras', model_name + '.tflite',
        'q_' + model_name + '.tflite'):
      self.assertTrue(os.path.exists(modelpath + filename), filename)
    leftover = [item for item in os.listdir(modelpath) if '_temp_' in item]
    self.assertEqual(leftover, [])

    # The quantized model must run on one of the exported images
    import numpy as np
    import tensorflow as tf
    interpreter = tf.lite.Interpreter(modelpath + 'q_' + model_name + '.tflite')
    interpreter.allocate_tensors()
    inp = interpreter.get_input_details()[0]
    out = interpreter.get_output_details()[0]
    xdim, ydim = inp['shape'][1], inp['shape'][2]
    cod_file = (self.school_dir + f'coded/{xdim}x{ydim}/'
      + self.export['frames'][0]['name'][:-4] + '.cod')
    img = tf.io.decode_jpeg(tf.io.read_file(cod_file)).numpy()
    scale, zero = inp['quantization']
    img = np.clip(np.round(img / scale + zero), -128, 127).astype(np.int8)
    interpreter.set_tensor(inp['index'], img[np.newaxis, ...])
    interpreter.invoke()
    result = interpreter.get_tensor(out['index'])
    self.assertEqual(result.shape[-1], 10)

    # --- school ----------------------------------------------------------------
    self.myschool.refresh_from_db()
    self.assertTrue(self.myschool.load_last_model)
    if self.myschool.model_type == self.myschool.model_train_type:
      self.assertEqual(self.myschool.last_fit, old_last_fit + 1)
