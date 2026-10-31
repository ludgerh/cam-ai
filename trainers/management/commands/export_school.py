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

# Exports a sample of a school (DB rows + files) for the training test in
# trainers/tests/test_train_school.py and for tune_school. Reads only, the
# school is not changed.
#
#   python manage.py export_school 8 --frames 200
#   python manage.py export_school 8 --frames 0     # all frames

import json
import os
from random import Random
from shutil import copyfile, rmtree
from django.core.management.base import BaseCommand, CommandError
from django.forms.models import model_to_dict
from tf_workers.models import school
from trainers.models import trainframe
from schools.models import tag

EXPORT_BASE = 'temp/test_schools/'

# Fields that point to other rows or are set by the test itself
SCHOOL_SKIP = ('id', 'creator', 'remote_creator', 'tf_worker', 'trainers', 'dir')
FRAME_SKIP = ('id', 'school', 'made_by', 'img_sizes')

class Command(BaseCommand):
  help = 'Export a sample of a school for the training test'

  def add_arguments(self, parser):
    parser.add_argument('school_id', type = int)
    parser.add_argument('--frames', type = int, default = 200,
      help = 'Number of frames, 0 = all')
    parser.add_argument('--seed', type = int, default = 1)
    parser.add_argument('--out', default = None,
      help = 'Target directory, default: ' + EXPORT_BASE + 'school<id>/')

  def handle(self, *args, **options):
    try:
      myschool = school.objects.get(id = options['school_id'])
    except school.DoesNotExist:
      raise CommandError('School #' + str(options['school_id']) + ' not found')
    outdir = options['out'] or EXPORT_BASE + 'school' + str(myschool.id) + '/'
    if not outdir.endswith('/'):
      outdir += '/'
    if os.path.exists(outdir):
      rmtree(outdir)
    os.makedirs(outdir)

    # Same selection as getlines() in the GPU trainer
    filterdict = {
      'school' : myschool.id,
      'deleted' : False,
      'train_status__gt' : 0,
    }
    if not myschool.ignore_checked:
      filterdict['checked'] = True
    frames = list(trainframe.objects.filter(**filterdict).order_by('id'))
    frames = [item for item in frames
      if os.path.exists(myschool.dir + 'frames/' + item.name)]
    if len(frames) < options['frames']:
      raise CommandError(
        f'School #{myschool.id} has only {len(frames)} usable frames')
    if options['frames'] == 0:
      sample = frames
    else:
      # Stratified by TR/VA so the validation split stays as in the school
      rng = Random(options['seed'])
      by_code = {}
      for item in frames:
        by_code.setdefault(item.code, []).append(item)
      sample = []
      for code, items in sorted(by_code.items()):
        count = round(options['frames'] * len(items) / len(frames))
        sample += rng.sample(items, min(count, len(items)))
      rest = [item for item in frames if item not in sample]
      while len(sample) < options['frames']:
        sample.append(rest.pop(rng.randrange(len(rest))))
      sample = sample[:options['frames']]

    coded_count = 0
    frame_rows = []
    for item in sample:
      src = myschool.dir + 'frames/' + item.name
      dst = outdir + 'frames/' + item.name
      os.makedirs(os.path.dirname(dst), exist_ok = True)
      copyfile(src, dst)
      coded_dir = myschool.dir + 'coded/'
      if os.path.exists(coded_dir):
        for size_dir in os.listdir(coded_dir):
          cod_src = coded_dir + size_dir + '/' + item.name[:-4] + '.cod'
          if os.path.exists(cod_src):
            cod_dst = outdir + 'coded/' + size_dir + '/' + item.name[:-4] + '.cod'
            os.makedirs(os.path.dirname(cod_dst), exist_ok = True)
            copyfile(cod_src, cod_dst)
            coded_count += 1
      row = model_to_dict(item, exclude = FRAME_SKIP)
      row['made'] = item.made.isoformat()
      frame_rows.append(row)

    model_file = myschool.dir + 'model/' + myschool.model_train_type + '.keras'
    if os.path.exists(model_file):
      os.makedirs(outdir + 'model/')
      copyfile(model_file, outdir + 'model/' + myschool.model_train_type + '.keras')

    school_row = model_to_dict(myschool, exclude = SCHOOL_SKIP)
    school_row['lastmodelfile'] = myschool.lastmodelfile.isoformat()
    tag_rows = [
      model_to_dict(item, exclude = ('id', ))
      for item in tag.objects.filter(school__in = (1, myschool.id)).order_by('id')
    ]
    with open(outdir + 'school.json', 'w') as f:
      json.dump({
        'school_id' : myschool.id,
        'school' : school_row,
        'tags' : tag_rows,
        'frames' : frame_rows,
      }, f, indent = 1)

    codes = {}
    for row in frame_rows:
      codes[row['code']] = codes.get(row['code'], 0) + 1
    self.stdout.write(
      f'School #{myschool.id} ({myschool.name}) -> {outdir}\n'
      f'  {len(frame_rows)} frames {codes}, {coded_count} coded files, '
      f'{len(tag_rows)} tags, model: {os.path.exists(model_file)}'
    )
