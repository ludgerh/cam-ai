# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

from django.db import models
from django.utils import timezone
from tf_workers.models import school

class stream(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=100, default='New Stream')
  made = models.DateTimeField(default=timezone.now)
  lastused = models.DateTimeField(default=timezone.now)

  cam_mode_flag = models.IntegerField(default=2)
  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  cam_view = models.BooleanField(default=True)
  cam_xres = models.IntegerField(default=0)
  cam_yres = models.IntegerField(default=0)
  cam_fpslimit = models.FloatField("FPS limit", default=2)
  cam_fpsactual = models.FloatField(default=0)
  cam_min_x_view = models.IntegerField(default=0)
  cam_max_x_view = models.IntegerField(default=0)
  cam_scale_x_view = models.FloatField(default=1.0)
  cam_feed_type = models.IntegerField("feed type", choices=((1, 'JPeg'), (2, 'Others'), (3, 'RTSP')), default=2)
  cam_url = models.CharField("video url", max_length=256, 
    default='rtmp://192.168.1.99/bcs/channel0_main.bcs?channel=0&stream=1&user=user1&password=password1')
  cam_apply_mask = models.BooleanField(default=False)
  cam_repeater = models.IntegerField(default=0)
  cam_checkdoubles = models.BooleanField(default=True)
  cam_latency = models.FloatField(default=60.0)
  cam_ffmpeg_fps = models.FloatField("ffmpeg FPS limit", default=0)
  cam_ffmpeg_segment = models.FloatField("ffmpeg segment length", default=10)
  cam_ffmpeg_crf = models.IntegerField("ffmpeg CRF", default=23)
  cam_video_codec = models.IntegerField(default=-1)
  cam_audio_codec = models.IntegerField(default=-1)
  cam_pause = models.BooleanField(default=False)
 
  det_mode_flag = models.IntegerField(default=2)
  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  det_view = models.BooleanField(default=True)
  det_fpslimit = models.FloatField("FPS limit", default=0)
  det_fpsactual = models.FloatField(default=0)
  det_min_x_view = models.IntegerField(default=0)
  det_max_x_view = models.IntegerField(default=0)
  det_scale_x_view = models.FloatField(default=1.0)
  det_threshold = models.IntegerField("threshold", default=40)
  det_backgr_delay = models.IntegerField("background delay", default=1)
  det_dilation = models.IntegerField("dilation", default=20)
  det_erosion = models.IntegerField("erosion", default=1)
  det_max_rect = models.IntegerField("max. number", default=20)
  det_max_size = models.IntegerField("max. size", default=100)
  det_apply_mask = models.BooleanField(default=False)
  det_scaledown = models.IntegerField("scaledown", default=0)
  # 0: automatic, epending on size, 1: switch off scaling

  eve_mode_flag = models.IntegerField(default=2)
  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  eve_view = models.BooleanField(default=True)
  eve_fpslimit = models.FloatField("FPS limit", default=0)
  eve_fpsactual = models.FloatField(default=0)
  eve_min_x_view = models.IntegerField(default=0)
  eve_max_x_view = models.IntegerField(default=0)
  eve_scale_x_view = models.FloatField(default=1.0)
  eve_alarm_email = models.CharField("alarm email", max_length=255, default='theo@tester123.de')
  eve_event_time_gap = models.IntegerField("new event gap", default=60)
  eve_margin = models.IntegerField("frame margin", default=20)
  eve_school = models.ForeignKey(school, on_delete=models.SET_DEFAULT, default=1)
  eve_all_predictions = models.BooleanField(default=True)

  def __str__(self):
    return('Stream model, name: '+self.name)
