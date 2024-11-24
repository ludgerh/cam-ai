"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

from django.db import models
from django.utils import timezone
from django.conf import settings
from tf_workers.models import school

class stream(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=100, default='New Stream')
  made = models.DateTimeField(default=timezone.now)
  demo = models.BooleanField(default=False)
  lastused = models.DateTimeField(default=timezone.now)
  creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_DEFAULT, default=1)
  storage_quota = models.BigIntegerField(default=0)
  encrypted = models.BooleanField(default=True)
  crypt_key = models.BinaryField(max_length=256, default=b'')

  cam_mode_flag = models.IntegerField(default=2)
  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  cam_view = models.BooleanField(default=True)
  #cam_is_virtual = models.BooleanField(default=False)
  cam_virtual_fps = models.FloatField(default=0.0) #0.0: Not virtual
  cam_xres = models.IntegerField(default=0)
  cam_yres = models.IntegerField(default=0)
  cam_fpslimit = models.FloatField("Image FPS limit", default=2.0)
  cam_fpsactual = models.FloatField(default=0)
  cam_min_x_view = models.IntegerField(default=0)
  cam_max_x_view = models.IntegerField(default=0)
  cam_scale_x_view = models.FloatField(default=1.0)
  cam_url = models.CharField("video url", max_length=256, default='')
  cam_apply_mask = models.BooleanField(default=False)
  cam_checkdoubles = models.BooleanField("Filter identical frames", default=True)
  cam_latency = models.FloatField(default=60.0)
  cam_ffmpeg_fps = models.FloatField("Video FPS limit", default=6)
  cam_ffmpeg_segment = models.FloatField("ffmpeg segment length", default=10)
  cam_ffmpeg_crf = models.IntegerField("ffmpeg CRF", default=23)
  cam_video_codec = models.IntegerField(default=-1)
  cam_audio_codec = models.IntegerField(default=-1)
  cam_pause = models.BooleanField(default=False)
  cam_control_mode = models.IntegerField(choices=((0, 'Url'), (1, 'ISAPI'), (2, 'ONVIF')), default=0)
  cam_control_ip = models.CharField(max_length=256, default='')
  cam_control_port = models.IntegerField(default=0)
  cam_control_user = models.CharField(max_length=256, default='')
  cam_control_passwd = models.CharField(max_length=256, default='')
  cam_red_lat = models.BooleanField("Reduce latence", default=True)
 
  det_mode_flag = models.IntegerField(default=2)
  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  det_view = models.BooleanField(default=True)
  det_fpslimit = models.FloatField("FPS limit", default=2.0)
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
  det_gpu_nr_cv = models.IntegerField(default=0)

  eve_mode_flag = models.IntegerField(default=2)
  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  eve_view = models.BooleanField(default=True)
  eve_fpslimit = models.FloatField("FPS limit", default=2.0)
  eve_fpsactual = models.FloatField(default=0)
  eve_min_x_view = models.IntegerField(default=0)
  eve_max_x_view = models.IntegerField(default=0)
  eve_scale_x_view = models.FloatField(default=1.0)
  eve_shrink_factor = models.FloatField("shrink factor", default=0.2) # 0.0 -> No Shrinking 1.0 50%
  eve_sync_factor = models.FloatField("sync factor", default=0.0) # in seconds
  eve_alarm_email = models.CharField("alarm email", max_length=255, default='')
  eve_event_time_gap = models.IntegerField("new event gap", default=60)
  eve_margin = models.IntegerField("frame margin", default=20)
  eve_school = models.ForeignKey(school, on_delete=models.SET_DEFAULT, default=1)
  eve_all_predictions = models.BooleanField(default=True)
  eve_gpu_nr_cv = models.IntegerField(default=0)

  def __str__(self):
    return('Stream model, name: '+self.name)
