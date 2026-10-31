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

# Level 1: pure training logic from the GPU plugin. No DB, no GPU, no redis.
# The plugin is not part of the repository, so the tests skip without it.

from unittest import skipIf
from django.test import SimpleTestCase

try:
  from plugins.train_worker_gpu.train_worker_gpu import (
    quantize_lr, is_better_score, next_stage_gamma, train_schedule,
    OVERFIT_BOTH_FALLING, OVERFIT_BOTH_RISING, OVERFIT_POSITIVE,
    OVERFIT_NEGATIVE, OVERFIT_SHORT,
  )
  plugin_missing = False
except ImportError:
  plugin_missing = True

PATIENCE = 8

def filled_schedule(bce_list, val_bce_list):
  s = train_schedule(patience = PATIENCE)
  for bce, val_bce in zip(bce_list, val_bce_list):
    s.next_values(bce, val_bce)
  return(s)

def falling(n = PATIENCE):
  return([1.0 - i * 0.1 for i in range(n)])

def rising(n = PATIENCE):
  return([0.2 + i * 0.1 for i in range(n)])

@skipIf(plugin_missing, 'plugins/train_worker_gpu not installed')
class QuantizeLrTest(SimpleTestCase):

  def test_powers_of_ten_unchanged(self):
    for lr in (1e-7, 1e-6, 1e-4, 1e-2, 1.0):
      self.assertAlmostEqual(quantize_lr(lr), lr)

  def test_half_steps(self):
    self.assertAlmostEqual(quantize_lr(3e-4), 10 ** -3.5)
    self.assertAlmostEqual(quantize_lr(2e-4), 10 ** -3.5)
    self.assertAlmostEqual(quantize_lr(1.5e-4), 1e-4)

  def test_zero(self):
    self.assertEqual(quantize_lr(0.0), 0.0)

  def test_negative_raises(self):
    with self.assertRaises(ValueError):
      quantize_lr(-1e-4)

@skipIf(plugin_missing, 'plugins/train_worker_gpu not installed')
class IsBetterScoreTest(SimpleTestCase):

  def test_fewer_errors_wins_regardless_of_bce(self):
    self.assertTrue(is_better_score(2, 0.9, 0.0, 3, 0.1, 0.0))
    self.assertFalse(is_better_score(3, 0.1, 0.0, 2, 0.9, 0.0))

  def test_bce_breaks_tie_with_same_gamma(self):
    self.assertTrue(is_better_score(2, 0.1, 1.0, 2, 0.2, 1.0))
    self.assertFalse(is_better_score(2, 0.2, 1.0, 2, 0.1, 1.0))

  def test_equal_is_not_better(self):
    self.assertFalse(is_better_score(2, 0.1, 1.0, 2, 0.1, 1.0))

  def test_margin(self):
    # 1 % better, but 2 % are required
    self.assertFalse(is_better_score(2, 0.099, 1.0, 2, 0.1, 1.0, margin = 0.02))
    self.assertTrue(is_better_score(2, 0.097, 1.0, 2, 0.1, 1.0, margin = 0.02))

  def test_tie_across_gammas_newer_wins(self):
    self.assertTrue(is_better_score(2, 0.9, 1.5, 2, 0.1, 1.0))

@skipIf(plugin_missing, 'plugins/train_worker_gpu not installed')
class NextStageGammaTest(SimpleTestCase):

  def test_raise_on_remaining_errors(self):
    self.assertEqual(next_stage_gamma(0.0, 0.0, 0.5, 3.0, recent_errors = 1), 0.5)

  def test_capped_at_max(self):
    self.assertEqual(next_stage_gamma(2.5, 2.5, 1.0, 3.0, recent_errors = 4), 3.0)

  def test_keep_without_errors(self):
    self.assertEqual(next_stage_gamma(1.0, 0.0, 0.5, 3.0, recent_errors = 0), 1.0)

  def test_never_below_min(self):
    self.assertEqual(next_stage_gamma(0.0, 1.0, 0.5, 3.0, recent_errors = 0), 1.0)

@skipIf(plugin_missing, 'plugins/train_worker_gpu not installed')
class TrainScheduleTest(SimpleTestCase):

  def test_short_history(self):
    s = filled_schedule(falling(PATIENCE - 1), falling(PATIENCE - 1))
    self.assertEqual(s.check_overfit(), OVERFIT_SHORT)
    self.assertTrue(s.check_range())
    self.assertEqual(s.check_volatility(), 0.0)
    self.assertEqual(s.check_volatility_trend(), 0.0)

  def test_both_falling(self):
    s = filled_schedule(falling(), falling())
    self.assertEqual(s.check_overfit(), OVERFIT_BOTH_FALLING)

  def test_both_rising(self):
    s = filled_schedule(rising(), rising())
    self.assertEqual(s.check_overfit(), OVERFIT_BOTH_RISING)

  def test_overfit_train_falls_val_rises(self):
    s = filled_schedule(falling(), rising())
    self.assertEqual(s.check_overfit(), OVERFIT_POSITIVE)

  def test_train_rises_val_falls(self):
    s = filled_schedule(rising(), falling())
    self.assertEqual(s.check_overfit(), OVERFIT_NEGATIVE)

  def test_history_limited_to_patience(self):
    s = filled_schedule(falling(PATIENCE * 2), falling(PATIENCE * 2))
    self.assertEqual(len(s.val_bce_history), PATIENCE)
    self.assertEqual(len(s.bce_history), PATIENCE)
    self.assertEqual(s.count_since_reset, PATIENCE * 2)

  def test_check_range(self):
    self.assertTrue(filled_schedule(falling(), falling()).check_range())
    flat = [0.5] * PATIENCE
    self.assertFalse(filled_schedule(flat, flat).check_range())

  def test_average_and_min(self):
    s = train_schedule(patience = PATIENCE)
    self.assertEqual(s.check_average(), 0.0)
    self.assertEqual(s.check_min(), float('inf'))
    s.next_values(0.5, 0.4)
    s.next_values(0.5, 0.2)
    self.assertAlmostEqual(s.check_average(), 0.3)
    self.assertAlmostEqual(s.check_min(), 0.2)

  def test_set_phase_resets_history(self):
    s = filled_schedule(falling(), falling())
    s.set_phase(1)
    self.assertEqual(s.phase, 1)
    self.assertEqual(s.val_bce_history, [])
    self.assertEqual(s.count_since_reset, 0)
    s = filled_schedule(falling(), falling())
    s.set_phase(2, reset_history = False)
    self.assertEqual(len(s.val_bce_history), PATIENCE)

  def test_volatility_trend(self):
    # Steps between epochs grow from 0.01 to 0.08 -> rising volatility
    steps = [0.01 * (i + 1) for i in range(PATIENCE - 1)]
    val = [1.0]
    for step in steps:
      val.append(val[-1] - step)
    s = filled_schedule(val, val)
    self.assertGreater(s.check_volatility_trend(), 0.0)
