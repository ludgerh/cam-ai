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

# Grid and result handling of the tune_school command. No DB, no training.

from django.test import SimpleTestCase
from trainers.management.commands.tune_school import (
  build_grid, combo_key, summarize,
)

def result_row(gamma_min, aug, repeat, errors, val_bce, status = 'Done'):
  return({
    'gamma_min' : str(gamma_min), 'gamma_step' : '0', 'gamma_max' : str(gamma_min),
    'aug' : str(aug), 'repeat' : str(repeat), 'status' : status,
    'val_errors' : str(errors), 'val_bce' : str(val_bce), 'minutes' : '90',
  })

class BuildGridTest(SimpleTestCase):

  def test_full_product(self):
    grid = build_grid([0.0, 1.0], [0.5], [3.0], [0.2, 0.3])
    self.assertEqual(grid, [
      (0.0, 0.5, 3.0, 0.2), (0.0, 0.5, 3.0, 0.3),
      (1.0, 0.5, 3.0, 0.2), (1.0, 0.5, 3.0, 0.3),
    ])

  def test_step_zero_ignores_max(self):
    grid = build_grid([0.0], [0.0], [2.0, 3.0], [0.3])
    self.assertEqual(grid, [(0.0, 0.0, 0.0, 0.3)])

  def test_max_not_above_min_is_constant(self):
    grid = build_grid([3.0], [0.5], [3.0], [0.3])
    self.assertEqual(grid, [(3.0, 0.0, 3.0, 0.3)])

  def test_default_grid_size(self):
    grid = build_grid([0.0, 1.0, 2.0], [0.0, 0.5], [3.0], [0.2, 0.3, 0.5])
    self.assertEqual(len(grid), 18)
    self.assertEqual(len(set(grid)), 18)

class ComboKeyTest(SimpleTestCase):

  def test_float_formatting_matches_csv(self):
    # The key from the grid must match the one read back from results.csv
    self.assertEqual(combo_key((0.0, 0.5, 3.0, 0.3), 2),
      combo_key((float('0'), float('0.5'), float('3'), float('0.3')), 2))

class SummarizeTest(SimpleTestCase):

  def test_sorted_by_errors_then_bce(self):
    summary = summarize([
      result_row(0, 0.3, 1, 4, 0.0020),
      result_row(0, 0.3, 2, 6, 0.0022),
      result_row(1, 0.3, 1, 5, 0.0030),
      result_row(1, 0.3, 2, 5, 0.0026),
      result_row(2, 0.3, 1, 5, 0.0040),
      result_row(2, 0.3, 2, 5, 0.0041),
    ])
    self.assertEqual([item['combo'][0] for item in summary], [0.0, 1.0, 2.0])
    self.assertEqual(summary[0]['errors_mean'], 5)
    self.assertEqual((summary[0]['errors_min'], summary[0]['errors_max']), (4, 6))
    self.assertAlmostEqual(summary[1]['val_bce_mean'], 0.0028)

  def test_failed_runs_are_ignored(self):
    summary = summarize([
      result_row(0, 0.3, 1, 4, 0.0020),
      result_row(0, 0.3, 2, 0, 0.0, status = 'Stopped'),
    ])
    self.assertEqual(summary[0]['runs'], 1)
