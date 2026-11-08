# trainers/tests/test_train_logic.py
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
from unittest.mock import MagicMock
from django.test import SimpleTestCase

try:
  from plugins.train_worker_gpu.train_worker_gpu import (
    quantize_lr, is_better_score, next_stage_gamma, next_finetuning,
    train_schedule, MyCallback,
    OVERFIT_BOTH_FALLING, OVERFIT_BOTH_RISING, OVERFIT_POSITIVE,
    OVERFIT_NEGATIVE, OVERFIT_SHORT, PHASE_START, PHASE_MAIN, PHASE_FINAL,
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

  def test_raise_from_current_gamma(self):
    gamma = 0.0
    ramp = []
    for i in range(8):
      gamma = next_stage_gamma(gamma, 0.0, 0.5, 3.0, recent_errors = 2)
      ramp.append(gamma)
    self.assertEqual(ramp, [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.0, 3.0])

  def test_zero_step_keeps_gamma(self):
    self.assertEqual(next_stage_gamma(0.0, 0.0, 0.0, 0.0, recent_errors = 5), 0.0)

  def test_capped_at_max(self):
    self.assertEqual(next_stage_gamma(2.5, 2.5, 1.0, 3.0, recent_errors = 4), 3.0)

  def test_keep_without_errors(self):
    self.assertEqual(next_stage_gamma(1.0, 0.0, 0.5, 3.0, recent_errors = 0), 1.0)

  def test_never_below_min(self):
    self.assertEqual(next_stage_gamma(0.0, 1.0, 0.5, 3.0, recent_errors = 0), 1.0)

@skipIf(plugin_missing, 'plugins/train_worker_gpu not installed')
class NextFinetuningTest(SimpleTestCase):

  def test_stages_efficientnetv2_b0(self):
    stages = [0]
    while stages[-1] < 349:
      stages.append(next_finetuning(stages[-1], 349))
    self.assertEqual(stages, [0, 10, 87, 349])

  def test_start_between_stages(self):
    self.assertEqual(next_finetuning(30, 349), 87)

  def test_small_model(self):
    self.assertEqual(next_finetuning(0, 10), 1)
    self.assertEqual(next_finetuning(1, 10), 2)

  def test_never_above_total(self):
    self.assertEqual(next_finetuning(349, 349), 349)

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

  def test_check_underfit(self):
    # Levels, not trends: training BCE at or above val BCE
    low = [0.1] * PATIENCE
    high = [0.2] * PATIENCE
    self.assertTrue(filled_schedule(high, low).check_underfit())
    self.assertTrue(filled_schedule(low, low).check_underfit())
    self.assertFalse(filled_schedule(low, high).check_underfit())
    s = filled_schedule(high[1:], low[1:])
    self.assertFalse(s.check_underfit())

  def test_underfit_ratio_ignores_val_spikes(self):
    val_bce = [0.1] * PATIENCE
    val_bce[3] = 3.0
    s = filled_schedule([0.2] * PATIENCE, val_bce)
    self.assertAlmostEqual(s.underfit_ratio(), 2.0)
    self.assertTrue(s.check_underfit())
    self.assertEqual(train_schedule(patience = PATIENCE).underfit_ratio(), 0.0)

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

  def test_final_done_at_lr_min(self):
    # At the minimum LR, width epochs without progress end the phase,
    # even while the range check alone would still continue
    s = train_schedule(patience = PATIENCE)
    self.assertEqual(s.width, 2)
    self.assertFalse(s.final_done(True, 1))
    self.assertTrue(s.final_done(True, 2))

  def test_final_done_above_lr_min(self):
    # Above the minimum LR only the range check counts
    s = train_schedule(patience = PATIENCE)
    self.assertFalse(s.final_done(False, 100))
    s = filled_schedule(falling(), falling())
    self.assertFalse(s.final_done(False, 100))
    s = filled_schedule(rising(), rising())
    self.assertTrue(s.final_done(False, 0))

@skipIf(plugin_missing, 'train_worker_gpu plugin not installed')
class MyCallbackStageTest(SimpleTestCase):

  def test_start_stage_keeps_global_best(self):
    # The fit record is filled from the epoch of the global best. A stage
    # without a new best must not lose it (fit was saved with epochs = 0
    # and the metrics of the last epoch).
    cb = MyCallback(MagicMock(), MagicMock(), MagicMock(), 0, patience = 12)
    self.assertEqual(cb.nr_to_save, 0)
    cb.nr_to_save = 266
    cb.best_name = 'model_temp_266.keras'
    cb.start_stage(0.0)
    self.assertEqual(cb.nr_to_save, 266)
    self.assertEqual(cb.best_name, 'model_temp_266.keras')

@skipIf(plugin_missing, 'train_worker_gpu plugin not installed')
class MyCallbackAugTest(SimpleTestCase):

  def callback(self, aug, bce_list, val_bce_list, phase = PHASE_MAIN):
    cb = MyCallback(MagicMock(), MagicMock(), MagicMock(), 0, patience = PATIENCE)
    cb.current_aug = aug
    cb.schedule = filled_schedule(bce_list, val_bce_list)
    cb.schedule.set_phase(phase, reset_history = False)
    return(cb)

  def test_lower_when_underfitting(self):
    cb = self.callback(0.6, [0.2] * PATIENCE, [0.1] * PATIENCE)
    self.assertTrue(cb.aug_lower_possible(OVERFIT_NEGATIVE))
    self.assertTrue(cb.aug_lower_possible(OVERFIT_BOTH_RISING))

  def test_no_lower_when_overfitting(self):
    cb = self.callback(0.6, [0.2] * PATIENCE, [0.1] * PATIENCE)
    self.assertFalse(cb.aug_lower_possible(OVERFIT_POSITIVE))

  def test_no_lower_without_underfit(self):
    cb = self.callback(0.6, [0.1] * PATIENCE, [0.2] * PATIENCE)
    self.assertFalse(cb.aug_lower_possible(OVERFIT_NEGATIVE))

  def test_no_lower_at_minimum(self):
    cb = self.callback(0.0, [0.2] * PATIENCE, [0.1] * PATIENCE)
    self.assertFalse(cb.aug_lower_possible(OVERFIT_NEGATIVE))
    # Rounding errors of repeated steps must not count as room to lower
    cb = self.callback(1e-17, [0.2] * PATIENCE, [0.1] * PATIENCE)
    self.assertFalse(cb.aug_lower_possible(OVERFIT_NEGATIVE))

  def test_no_lower_outside_main_phase(self):
    cb = self.callback(
      0.6, [0.2] * PATIENCE, [0.1] * PATIENCE, phase = PHASE_START)
    self.assertFalse(cb.aug_lower_possible(OVERFIT_NEGATIVE))

@skipIf(plugin_missing, 'train_worker_gpu plugin not installed')
class MyCallbackAugCarryOverTest(SimpleTestCase):

  def test_next_stage_keeps_augmentation(self):
    # The start value from the school only applies to the first stage,
    # later stages continue with the augmentation the last one ended with
    myschool = MagicMock(model_image_augmentation = 0.6, model_gamma = 0.0)
    cb = MyCallback(MagicMock(), MagicMock(), myschool, 0, patience = PATIENCE)
    model = MagicMock()
    cb.set_model(model)
    cb.set_params({'steps' : 10})
    cb.on_epoch_begin(0)
    self.assertAlmostEqual(cb.current_aug, 0.6)
    self.assertAlmostEqual(cb.best_aug, 0.6)
    cb.current_aug = 0.4
    cb.start_stage(0.0)
    self.assertAlmostEqual(cb.best_aug, 0.4)
    cb.on_epoch_begin(1)
    self.assertAlmostEqual(cb.current_aug, 0.4)
    aug_layer = model.get_layer.return_value
    aug_layer.magnitude.assign.assert_called_with(12.0)

@skipIf(plugin_missing, 'train_worker_gpu plugin not installed')
class MyCallbackMainPhaseTest(SimpleTestCase):

  def callback(self, aug, bce_list, val_bce_list, no_improve = 0):
    cb = MyCallback(MagicMock(), MagicMock(), MagicMock(), 0, patience = PATIENCE)
    cb.set_model(MagicMock())
    cb.current_aug = aug
    cb.best_aug = aug
    cb.schedule = filled_schedule(bce_list, val_bce_list)
    cb.schedule.set_phase(PHASE_MAIN, reset_history = False)
    cb.no_improve_count = no_improve
    return(cb)

  def test_lower_before_stage_end(self):
    # Underfitting lowers the augmentation while the stage still improves.
    # Training BCE twice the val BCE halves the augmentation.
    cb = self.callback(0.8, [0.2] * PATIENCE, [0.1] * PATIENCE)
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_NEGATIVE), 0.4)
    self.assertEqual(cb.schedule.phase, PHASE_MAIN)
    self.assertEqual(cb.schedule.val_bce_history, [])
    self.assertAlmostEqual(cb.ave_before_aug_change, 0.1)

  def test_lower_at_least_one_step(self):
    cb = self.callback(0.8, [0.105] * PATIENCE, [0.1] * PATIENCE)
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_NEGATIVE), 0.7)

  def test_lower_on_grid(self):
    # 0.3 / 1.8 = 0.17 is rounded down to the 0.1 grid
    cb = self.callback(0.3, [0.18] * PATIENCE, [0.1] * PATIENCE)
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_NEGATIVE), 0.1)

  def test_lower_not_below_minimum(self):
    cb = self.callback(0.1, [0.5] * PATIENCE, [0.1] * PATIENCE)
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_NEGATIVE), 0.0)

  def test_no_lower_if_last_change_did_not_help(self):
    cb = self.callback(0.8, [0.2] * PATIENCE, [0.1] * PATIENCE)
    cb.ave_before_aug_change = 0.1
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_NEGATIVE), 0.8)
    self.assertEqual(cb.schedule.phase, PHASE_MAIN)
    self.assertEqual(len(cb.schedule.val_bce_history), PATIENCE)

  def test_no_raise_before_stage_end(self):
    cb = self.callback(0.4, falling(), [0.1] * PATIENCE)
    cb.stage_best_bce = 0.1
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_POSITIVE), 0.4)
    self.assertEqual(cb.schedule.phase, PHASE_MAIN)

  def test_final_takes_augmentation_of_stage_best(self):
    # The final phase continues from the stage best weights and must use
    # the augmentation they were trained with, not that of the global best
    cb = self.callback(
      0.4, [0.05] * PATIENCE, [0.1] * PATIENCE, no_improve = PATIENCE)
    cb.best_aug = 0.6
    cb.stage_best_weights = ['weights']
    cb.stage_best_aug = 0.5
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_BOTH_FALLING), 0.5)
    self.assertEqual(cb.schedule.phase, PHASE_FINAL)
    cb.model.set_weights.assert_called_once_with(['weights'])

  def test_final_without_stage_best_keeps_augmentation(self):
    cb = self.callback(
      0.4, [0.05] * PATIENCE, [0.1] * PATIENCE, no_improve = PATIENCE)
    cb.best_aug = 0.6
    self.assertAlmostEqual(cb.main_phase_step(OVERFIT_BOTH_FALLING), 0.4)
    self.assertEqual(cb.schedule.phase, PHASE_FINAL)
