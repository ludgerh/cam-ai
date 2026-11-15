# config/tests.py
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

from unittest.mock import patch
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from core.models import plugin as plugin_db
from streams.models import stream
from . import views

class plugins_post_test(TestCase):

  def setUp(self):
    self.user = User.objects.create_superuser('plugintest', 'plugintest@example.com', 'pw')
    self.det = [plugin_db.objects.create(type = 'D', name = 'det' + str(i),
      version = '1', maker = 'm', copyright = 'c', description = 'd',
      path = 'p') for i in range(2)]
    self.alarm = [plugin_db.objects.create(type = 'A', name = 'alarm' + str(i),
      version = '1', maker = 'm', copyright = 'c', description = 'd',
      path = 'p') for i in range(2)]
    self.streams = [stream.objects.create(name = 's' + str(i), active = True,
      det_plugin = self.det[0], eve_alarm_plugin = self.alarm[0])
      for i in range(3)]

  def post(self, data):
    request = RequestFactory().post('/config/plugins/', data)
    request.user = self.user
    # access is only initialized in the running server
    with (patch.object(views, 'Thread') as thread,
        patch.object(views, 'access') as access):
      access.check.return_value = True
      views.plugins.as_view()(request)
    return(thread)

  def test_changed_streams_restart(self):
    """
    Only streams with a changed plugin are saved and restarted, each once
    """
    s0, s1, s2 = self.streams
    thread = self.post({
      'det_plugin_' + str(s0.id) : self.det[1].id,
      'alarm_plugin_' + str(s0.id) : self.alarm[1].id,
      'det_plugin_' + str(s1.id) : self.det[0].id,
      'alarm_plugin_' + str(s2.id) : self.alarm[1].id,
    })
    s0.refresh_from_db()
    s2.refresh_from_db()
    self.assertEqual(s0.det_plugin_id, self.det[1].id)
    self.assertEqual(s0.eve_alarm_plugin_id, self.alarm[1].id)
    self.assertEqual(s2.eve_alarm_plugin_id, self.alarm[1].id)
    thread.assert_called_once()
    self.assertEqual(thread.call_args.kwargs['args'], ([s0.id, s2.id], ))
    thread.return_value.start.assert_called_once()

  def test_unchanged_no_restart(self):
    """
    Submitting the current selection restarts nothing
    """
    data = {}
    for s_item in self.streams:
      data['det_plugin_' + str(s_item.id)] = self.det[0].id
    thread = self.post(data)
    thread.assert_not_called()

  def test_restart_streams(self):
    """
    restart_streams hands the streams to the startup process one by one
    """
    calls = []
    with (patch.object(views.startup_redis, 'get_start_stream_busy',
        return_value = 0),
        patch.object(views.startup_redis, 'set_start_stream_busy',
          side_effect = calls.append)):
      views.restart_streams([3, 5])
    self.assertEqual(calls, [3, 5])
