from django.db import models
from django.utils import timezone

class stream(models.Model):
  active = models.BooleanField(default=True)
  name = models.CharField(max_length=100, default='New Stream')
  made = models.DateTimeField(default=timezone.now)
  lastused = models.DateTimeField(default=timezone.now)

  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  cam_mode_flag = models.IntegerField(default=2)
  cam_view = models.BooleanField(default=True)
  cam_xres = models.IntegerField(default=0)
  cam_yres = models.IntegerField(default=0)
  cam_fpslimit = models.FloatField("FPS limit", default=0)
  cam_fpsactual = models.FloatField(default=0)
  cam_feed_type = models.IntegerField("feed type", choices=((1, 'JPeg'), (2, 'Others'), (3, 'RTSP')), default=2)
  cam_url = models.CharField("video url", max_length=256, default='')
  cam_apply_mask = models.BooleanField(default=False)
  cam_repeater = models.IntegerField(default=0)
  cam_checkdoubles = models.BooleanField(default=True)
  cam_latency = models.FloatField(default=60.0)
  cam_ffmpeg_fps = models.FloatField("ffmpeg FPS limit", default=0)
  cam_ffmpeg_segment = models.FloatField("ffmpeg segment length", default=10)
  cam_ffmpeg_crf = models.IntegerField("ffmpeg CRF", default=23)
  cam_video_codec = models.IntegerField(default=-1)
  cam_audio_codec = models.IntegerField(default=-1)

  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  det_mode_flag = models.IntegerField(default=1)
  det_view = models.BooleanField(default=True)
  det_fpslimit = models.FloatField("FPS limit", default=0)
  det_fpsactual = models.FloatField(default=0)
  det_threshold = models.IntegerField("threshold", default=70)
  det_backgr_delay = models.IntegerField("background delay", default=3)
  det_dilation = models.IntegerField("dilation", default=50)
  det_erosion = models.IntegerField("erosion", default=2)
  det_max_rect = models.IntegerField("max. number", default=10)
  det_max_size = models.IntegerField("max. size", default=100)
  det_apply_mask = models.BooleanField(default=False)

  # 0: Not active  1: Runnin in parents process  2: Running in own process  
  eve_mode_flag = models.IntegerField(default=1)
  eve_view = models.BooleanField(default=True)
  eve_fpslimit = models.FloatField("FPS limit", default=0)
  eve_fpsactual = models.FloatField(default=0)
  eve_alarm_email = models.CharField("alarm email", max_length=255, default='')
  eve_event_time_gap = models.IntegerField("new event gap", default=60)
  eve_margin = models.IntegerField("frame margin", default=50)
  eve_school = models.IntegerField("school", default=1)
  eve_all_predictions = models.BooleanField(default=False)

  def __str__(self):
    return('Stream model, name: '+self.name)
