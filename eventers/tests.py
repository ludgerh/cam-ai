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
from django.test import SimpleTestCase
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
