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

# Grid search over gamma_min, gamma_step, gamma_max and the start value of
# the image augmentation for one school. Every combination is trained
# completely (all finetuning stages) and repeated, because single runs
# differ by about +-2 validation errors by chance alone.
#
#   python manage.py export_school 8 --frames 0
#   python manage.py tune_school temp/test_schools/school8/ --dry-run
#   python manage.py tune_school temp/test_schools/school8/ --gpu 0
#
# Isolation: the runs use their own test database (test_camai_tune) and a
# copy of the export, so neither the live DB nor data/schools/ is touched.
# The live trainers should be stopped, otherwise they share the GPU.
#
# Resume: results.csv is written after every run. Starting the command again
# with the same --out skips the runs that already ended with status Done.

import csv
import json
import os
import statistics
from itertools import product
from multiprocessing import Process
from shutil import copy2, copytree, rmtree
from time import time
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, connections
from django.utils.dateparse import parse_datetime

TEST_DB_NAME = 'test_camai_tune'

RESULT_FIELDS = [
  'gamma_min', 'gamma_step', 'gamma_max', 'aug', 'repeat', 'status',
  'val_errors', 'val_bce', 'val_recall', 'val_precision', 'best_epoch',
  'epochs', 'minutes', 'log',
]

LOG_HEADER = ('#\tPh\tSec\tLR\tBCE \tFT\tAugm\tGamma\tBinAcc\tRec\tPrec \t'
  'val_BCE\tval_BinAcc\tval_Rec\tval_Prec \tval_Err\n')

def build_grid(gamma_mins, gamma_steps, gamma_maxs, augs):
  """
  All parameter combinations without duplicates. With step 0 or
  gamma_max <= gamma_min gamma stays constant, so these collapse to
  (gamma_min, 0, gamma_min).
  """
  result = []
  for gamma_min, gamma_step, gamma_max, aug in product(
      gamma_mins, gamma_steps, gamma_maxs, augs):
    if gamma_step <= 0.0 or gamma_max <= gamma_min:
      gamma_step = 0.0
      gamma_max = gamma_min
    combo = (gamma_min, gamma_step, gamma_max, aug)
    if combo not in result:
      result.append(combo)
  return(result)

def combo_key(combo, repeat):
  return(tuple(f'{value:g}' for value in combo) + (str(repeat), ))

def read_results(filename):
  if not os.path.exists(filename):
    return([])
  with open(filename, newline = '') as f:
    return(list(csv.DictReader(f)))

def summarize(rows):
  """
  One line per combination, best first. Primary criterion is the mean
  number of validation errors, the gamma-independent val_bce breaks ties
  (as is_better_score() in the GPU trainer does).
  """
  combos = {}
  for row in rows:
    if row['status'] != 'Done':
      continue
    key = (float(row['gamma_min']), float(row['gamma_step']),
      float(row['gamma_max']), float(row['aug']))
    combos.setdefault(key, []).append(row)
  result = []
  for key, items in combos.items():
    errors = [int(item['val_errors']) for item in items]
    bces = [float(item['val_bce']) for item in items]
    result.append({
      'combo' : key,
      'runs' : len(items),
      'errors_mean' : statistics.mean(errors),
      'errors_min' : min(errors),
      'errors_max' : max(errors),
      'val_bce_mean' : statistics.mean(bces),
      'minutes_mean' : statistics.mean(float(item['minutes']) for item in items),
    })
  result.sort(key = lambda item: (item['errors_mean'], item['val_bce_mean']))
  return(result)

def format_summary(summary):
  lines = [
    'gamma_min  gamma_step  gamma_max   aug  runs  errors (min-max)'
    '  val_bce    minutes',
  ]
  for item in summary:
    gamma_min, gamma_step, gamma_max, aug = item['combo']
    lines.append(
      f'{gamma_min:9.2f}  {gamma_step:10.2f}  {gamma_max:9.2f}  {aug:4.2f}'
      f'  {item["runs"]:4d}  {item["errors_mean"]:6.1f} '
      f'({item["errors_min"]}-{item["errors_max"]})'
      f'  {item["val_bce_mean"]:.6f}  {item["minutes_mean"]:7.0f}'
    )
  return('\n'.join(lines))

class fake_djconf():
  # Config values for the training process, so the live settings
  # (e.g. tr_epochs, datapath) do not leak in.

  def __init__(self, values):
    self.values = values

  def getconfig(self, param, default = None, forcedb = False):
    return(self.values.get(param, default))

  getconfigint = getconfig
  getconfigfloat = getconfig
  getconfigbool = getconfig

def run_training(db_name, school_id, fit_id, gpu_nr, gpu_mem_limit, config):
  # Runs in its own process, like the live trainers: TensorFlow and the GPU
  # memory are released completely after every run. manage.py sets the start
  # method to 'spawn', so Django is set up again here and the settings point
  # to the live DB: switch to the test DB before the first query.
  import django
  from django.conf import settings
  if not db_name.startswith('test_'):
    raise RuntimeError('Refusing to train on database ' + db_name)
  settings.DATABASES['default']['NAME'] = db_name
  django.setup()
  if connection.settings_dict['NAME'] != db_name:
    raise RuntimeError('Not connected to ' + db_name)
  from unittest.mock import patch
  from tf_workers.models import school
  from trainers.models import fit
  from plugins.train_worker_gpu import train_worker_gpu
  config['version'] = train_worker_gpu.version
  with (
    patch('plugins.train_worker_gpu.train_worker_gpu.djconf',
      fake_djconf(config)),
    # Quota needs the disk usage from the live redis
    patch('users.userinfo.free_quota', lambda myuser: 1),
  ):
    myschool = school.objects.get(id = school_id)
    myfit = fit.objects.get(id = fit_id)
    train_worker_gpu.train_once_gpu(myschool, myfit, gpu_nr, gpu_mem_limit)

def link_or_copy(src, dst):
  # The frames are only read: hard links save time and disk space
  try:
    os.link(src, dst)
  except OSError:
    copy2(src, dst)

class Command(BaseCommand):
  help = 'Grid search over gamma and augmentation for one exported school'

  def add_arguments(self, parser):
    parser.add_argument('export_dir',
      help = 'Export of the school (python manage.py export_school ID --frames 0)')
    parser.add_argument('--gamma-min', type = float, nargs = '+',
      default = [0.0, 1.0, 2.0])
    parser.add_argument('--gamma-step', type = float, nargs = '+',
      default = [0.0, 0.5])
    parser.add_argument('--gamma-max', type = float, nargs = '+',
      default = [3.0])
    parser.add_argument('--aug', type = float, nargs = '+',
      default = [0.2, 0.3, 0.5],
      help = 'Start value of the image augmentation')
    parser.add_argument('--repeats', type = int, default = 2)
    parser.add_argument('--from-last-model', action = 'store_true',
      help = 'Continue from the exported model instead of a new one')
    parser.add_argument('--gpu', type = int, default = 0,
      help = 'GPU number, -1 = CPU')
    parser.add_argument('--gpu-mem-limit', type = int, default = 0)
    parser.add_argument('--out', default = None,
      help = 'Result directory, default: temp/tune_schools/<export name>/')
    parser.add_argument('--dry-run', action = 'store_true',
      help = 'Only list the runs')

  def handle(self, *args, **options):
    export_dir = options['export_dir']
    if not export_dir.endswith('/'):
      export_dir += '/'
    if not os.path.exists(export_dir + 'school.json'):
      raise CommandError('No school export in ' + export_dir)
    outdir = options['out'] or ('temp/tune_schools/'
      + os.path.basename(export_dir.rstrip('/')) + '/')
    if not outdir.endswith('/'):
      outdir += '/'
    results_file = outdir + 'results.csv'

    grid = build_grid(options['gamma_min'], options['gamma_step'],
      options['gamma_max'], options['aug'])
    done = {combo_key(
        (float(row['gamma_min']), float(row['gamma_step']),
        float(row['gamma_max']), float(row['aug'])), int(row['repeat']))
      for row in read_results(results_file) if row['status'] == 'Done'}
    runs = [(combo, repeat)
      for repeat in range(1, options['repeats'] + 1)
      for combo in grid
      if combo_key(combo, repeat) not in done]
    self.stdout.write(f'{len(grid)} combinations x {options["repeats"]} repeats, '
      f'{len(runs)} runs to do ({len(done)} already done)')
    for combo, repeat in runs:
      self.stdout.write('  gamma %g / %g / %g, aug %g, repeat %d'
        % (combo + (repeat, )))
    if options['dry_run'] or not runs:
      if done:
        self.stdout.write('\n' + format_summary(summarize(
          read_results(results_file))))
      return

    os.makedirs(outdir + 'logs/', exist_ok = True)
    workdir = outdir + 'work/'
    if os.path.exists(workdir):
      rmtree(workdir)
    self.stdout.write('Copying ' + export_dir + ' -> ' + workdir)
    copytree(export_dir, workdir, copy_function = link_or_copy)
    with open(export_dir + 'school.json') as f:
      export = json.load(f)

    test_settings = connection.settings_dict.setdefault('TEST', {})
    test_settings['NAME'] = TEST_DB_NAME
    old_name = connection.creation.create_test_db(
      verbosity = 1, autoclobber = True, serialize = False)
    try:
      school_id = self.load_export(export, workdir)
      self.run_grid(runs, school_id, export_dir, workdir, outdir,
        results_file, options)
    finally:
      connections.close_all()
      connection.creation.destroy_test_db(old_name, verbosity = 1)
      rmtree(workdir, True)
    self.stdout.write('\n' + format_summary(summarize(
      read_results(results_file))))

  def load_export(self, export, workdir):
    # Same as the setUp() of trainers/tests/test_train_school.py
    from django.contrib.auth.models import User
    from tf_workers.models import worker, school
    from trainers.models import trainframe
    from schools.models import tag
    user = User.objects.create(username = 'tuner')
    myworker = worker.objects.create()
    school_row = dict(export['school'])
    school_row['lastmodelfile'] = parse_datetime(school_row['lastmodelfile'])
    school_row['model_finetuning'] = -2
    # Only the metrics are needed, this skips the TFLite export
    school_row['save_new_model'] = False
    myschool = school.objects.create(
      creator = user,
      remote_creator = user,
      tf_worker = myworker,
      dir = os.path.abspath(workdir) + '/',
      **school_row,
    )
    tag.objects.all().delete()
    for row in export['tags']:
      if row['school'] != 1:
        row['school'] = myschool.id
      tag.objects.create(**row)
    frames = []
    for row in export['frames']:
      row = dict(row)
      row['made'] = parse_datetime(row['made'])
      frames.append(trainframe(school = myschool.id, **row))
    trainframe.objects.bulk_create(frames)
    self.stdout.write(f'Loaded school "{myschool.name}" with {len(frames)} frames')
    return(myschool.id)

  def run_grid(self, runs, school_id, export_dir, workdir, outdir,
      results_file, options):
    from tf_workers.models import school
    from trainers.models import fit
    datapath = os.path.abspath(outdir) + '/data/'
    config = {
      'tr_epochs' : 1000000,
      'tr_batchsize' : 32,
      'validation_split' : 0.33333333,
      'schools_backup' : False,
      'datapath' : datapath,
      'schools_dir' : datapath + 'schools/',
    }
    durations = []
    for count, (combo, repeat) in enumerate(runs, 1):
      gamma_min, gamma_step, gamma_max, aug = combo
      name = 'g%g-%g-%g_a%g_r%d' % (combo + (repeat, ))
      eta = ''
      if durations:
        eta = (', about %.1f h left'
          % (statistics.mean(durations) * (len(runs) - count + 1) / 3600))
      self.stdout.write(f'\n[{count}/{len(runs)}] {name}{eta}')
      # Every run starts from the same model files
      rmtree(workdir + 'model/', True)
      if os.path.exists(export_dir + 'model/'):
        copytree(export_dir + 'model/', workdir + 'model/')
      school.objects.filter(id = school_id).update(
        model_gamma = gamma_min,
        model_gamma_step = gamma_step,
        model_gamma_max = gamma_max,
        model_image_augmentation = aug,
        load_last_model = options['from_last_model'],
      )
      myschool = school.objects.get(id = school_id)
      myfit = fit.objects.create(
        school = school_id,
        model_image_augmentation = aug,
        model_gamma = gamma_min,
        model_gamma_step = gamma_step,
        model_gamma_max = gamma_max,
        model_finetuning = myschool.model_finetuning,
        status = 'Waiting',
      )
      connections.close_all()
      start = time()
      process = Process(target = run_training, args = (
        connection.settings_dict['NAME'], school_id, myfit.id,
        options['gpu'], options['gpu_mem_limit'], dict(config)))
      process.start()
      try:
        process.join()
      except KeyboardInterrupt:
        process.terminate()
        process.join()
        raise
      durations.append(time() - start)
      myfit.refresh_from_db()
      logfile = outdir + 'logs/' + name + '.log'
      self.write_log(myfit, logfile)
      row = {
        'gamma_min' : f'{gamma_min:g}',
        'gamma_step' : f'{gamma_step:g}',
        'gamma_max' : f'{gamma_max:g}',
        'aug' : f'{aug:g}',
        'repeat' : repeat,
        'status' : myfit.status,
        'val_errors' : myfit.val_errors,
        'val_bce' : myfit.val_bce,
        'val_recall' : myfit.val_recall,
        'val_precision' : myfit.val_precision,
        'best_epoch' : myfit.epochs,
        'epochs' : myfit.epoch_set.count(),
        'minutes' : round(durations[-1] / 60.0, 1),
        'log' : logfile,
      }
      new_file = not os.path.exists(results_file)
      with open(results_file, 'a', newline = '') as f:
        writer = csv.DictWriter(f, fieldnames = RESULT_FIELDS)
        if new_file:
          writer.writeheader()
        writer.writerow(row)
      self.stdout.write(f'  {myfit.status}: {myfit.val_errors} errors, '
        f'val_bce {myfit.val_bce:.6f}, {row["epochs"]} epochs, '
        f'{row["minutes"]} min')

  def write_log(self, myfit, logfile):
    # Same columns as the epoch logs used for the gamma comparison
    with open(logfile, 'w') as f:
      f.write(LOG_HEADER)
      for count, item in enumerate(myfit.epoch_set.order_by('id'), 1):
        f.write('\t'.join((
          str(count), str(item.phase), f'{item.seconds:.0f}',
          f'{item.learning_rate:.1f}', f'{item.bce:.4g}',
          str(item.finetuning), f'{item.augmentation:.4f}',
          f'{item.gamma:.3f}', f'{item.binacc:.4f}', f'{item.recall:.4f}',
          f'{item.precision:.4f}', f'{item.val_bce:.4g}',
          f'{item.val_binacc:.4f}', f'{item.val_recall:.4f}',
          f'{item.val_precision:.4f}', str(item.val_errors),
        )) + '\n')
