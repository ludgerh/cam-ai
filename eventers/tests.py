# eventers/tests.py
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

import asyncio
from collections import OrderedDict
from threading import Lock as t_lock
from time import time
from django.test import SimpleTestCase
from eventers.c_event import c_event
from eventers.c_eventers import eve_worker

class fake_shared_mem():
  def __init__(self, time_gap):
    self.time_gap = time_gap

  def read_1_meta(self, key):
    return(self.time_gap)

class fake_event(list):
  # Just what merge_events() touches
  def __init__(self, box, ts, nr_frames = 1):
    super().__init__(box)
    self.last_box = list(box)
    self.start = ts
    self.end = ts
    self.check_out_ts = None
    self.frames = {(ts, i) : None for i in range(nr_frames)}

  def merge_frames(self, the_other_one):
    self.frames.update(the_other_one.frames)

class MergeEventsTest(SimpleTestCase):

  def make_worker(self, match_area = True, close_items = 0):
    # No process, no queues: merge_events() only needs these attributes
    worker = eve_worker.__new__(eve_worker)
    worker.shared_mem = fake_shared_mem(10)
    worker.event_match_area = match_area
    worker.event_close_items = close_items
    worker.event_dict = {}
    return(worker)

  def test_distant_events_stay_apart(self):
    worker = self.make_worker()
    worker.event_dict = {
      1 : fake_event([0, 10, 0, 10], 1.0),
      2 : fake_event([100, 110, 100, 110], 2.0),
    }
    asyncio.run(worker.merge_events())
    self.assertEqual(len(worker.event_dict), 2)

  def test_distant_events_merge_without_area_matching(self):
    worker = self.make_worker(match_area = False)
    worker.event_dict = {
      1 : fake_event([0, 10, 0, 10], 1.0),
      2 : fake_event([100, 110, 100, 110], 2.0),
    }
    asyncio.run(worker.merge_events())
    self.assertEqual(list(worker.event_dict), [1])
    self.assertEqual(len(worker.event_dict[1].frames), 2)

  def test_close_after_items(self):
    worker = self.make_worker(close_items = 8)
    worker.event_dict = {
      1 : fake_event([0, 10, 0, 10], 1.0, nr_frames = 7),
      2 : fake_event([100, 110, 100, 110], 2.0, nr_frames = 8),
    }
    asyncio.run(worker.merge_events())
    self.assertIsNone(worker.event_dict[1].check_out_ts)
    self.assertEqual(worker.event_dict[2].check_out_ts, 2.0)

  def test_no_close_by_default(self):
    worker = self.make_worker()
    worker.event_dict = {1 : fake_event([0, 10, 0, 10], 1.0, nr_frames = 100)}
    asyncio.run(worker.merge_events())
    self.assertIsNone(worker.event_dict[1].check_out_ts)

class CheckOutDueTest(SimpleTestCase):

  def make_worker(self):
    worker = eve_worker.__new__(eve_worker)
    worker.shared_mem = fake_shared_mem(1)
    worker.event_max_time = 30.0
    worker.event_name = 'Lid open'
    return(worker)

  def make_event(self, capture_age, add_age):
    item = fake_event([0, 10, 0, 10], time() - capture_age)
    item.name = 'Lid open'
    item.last_add_ts = time() - add_age
    return(item)

  def test_delayed_frames_keep_the_event_open(self):
    # Captured 3 s ago, but just arrived: the processing delay must not count
    worker = self.make_worker()
    self.assertFalse(worker.check_out_due(self.make_event(3.0, 0.2)))

  def test_close_after_gap_without_new_frames(self):
    worker = self.make_worker()
    self.assertTrue(worker.check_out_due(self.make_event(3.0, 1.5)))

  def test_close_on_name_change(self):
    worker = self.make_worker()
    item = self.make_event(0.0, 0.0)
    item.name = 'Lid closed'
    self.assertTrue(worker.check_out_due(item))

  def test_merge_keeps_latest_add_time(self):
    first = c_event.__new__(c_event)
    second = c_event.__new__(c_event)
    for item, add_ts in ((first, 10.0), (second, 20.0)):
      item.event_lock = t_lock()
      item.frames = OrderedDict()
      item.last_box = [0, 10, 0, 10]
      item.last_box_ts = 0.0
      item.last_add_ts = add_ts
      item.focus_max = 0.0
      item.append(None)
      item.append(None)
      item.append(None)
      item.append(None)
      item.append([])
    first.merge_frames(second)
    self.assertEqual(first.last_add_ts, 20.0)
