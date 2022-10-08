import sys
import cv2 as cv
import numpy as np
import json
from psutil import Process
from signal import SIGINT, SIGKILL
from os import remove, path, makedirs, mkfifo, kill as oskill
from shutil import move
from time import sleep, time
from setproctitle import setproctitle
from logging import getLogger
from multitimer import MultiTimer
from traceback import format_exc
from glob import glob
from threading import Thread
from subprocess import Popen, PIPE, DEVNULL
from django.db import connection
from django.db.utils import OperationalError
from tools.c_logger import log_ini
from tools.l_tools import djconf, ts2filename, NonBlockingStreamReader
from viewers.c_viewers import c_viewer
from .c_devices import c_device
from .models import stream

class c_cam(c_device):
  def __init__(self, *args, **kwargs):
    self.type = 'C'
    super().__init__(*args, **kwargs)
    self.mode_flag = self.dbline.cam_mode_flag
    self.cam_active = False
    self.cam_recording = False
    self.ff_proc = None
    self.getting_newprozess = False
    self.wd_proc = None
    self.mp4_proc = None
    self.do_run = True
    self.finished = False
    self.recordingspath = djconf.getconfig('recordingspath', 'data/recordings/')
    self.framewait = 0.0
    if not path.exists(self.recordingspath):
      makedirs(self.recordingspath)
    if self.dbline.cam_view:
      self.viewer = c_viewer(self, self.logger)
    else:
      self.viewer = None

  def in_queue_handler(self, received):
    if super().in_queue_handler(received):
      return(True)
    else:
      if (received[0] == 'reset_cam'):
        self.reset_cam()
      else:
        return(False)
      return(True)

  def run_one(self):
    if not self.do_run:
      return(None)
    thistime = time()
    while True:
      if not self.redis.check_if_counts_zero('C', self.dbline.id):
        if self.cam_active:
          if ((not self.redis.record_from_dev('C', self.dbline.id)) 
              and self.cam_recording):
            self.stopprocess()
            self.newprocess() 
            self.cam_recording = False
            self.logger.info('Cam #'+str(self.dbline.id)+' stopped recording')
          if (self.redis.record_from_dev('C', self.dbline.id) 
              and (not self.cam_recording)):
            self.stopprocess()
            self.newprocess() 
            self.cam_recording = True
            self.logger.info('Cam #'+str(self.dbline.id)+' started recording')
        else:
          self.newprocess() 
          self.logger.info('Cam #'+str(self.dbline.id)+' is on')
          self.cam_active = True
        self.cam_ts = None
        break
      else:
        if self.cam_active:
          if self.cam_ts is None:
            self.cam_ts = time()
            break
          else:
            if (time() - self.cam_ts) < 60:
              break
            else:
              self.logger.info('Cam #'+str(self.dbline.id)+' is off')
              self.cam_active = False
              self.cam_ts = None
              self.stopprocess()
        else:
          if not self.do_run:
            return(None)
          sleep(djconf.getconfigfloat('short_brake', 0.01))
    while True:
      if self.dbline.cam_feed_type == 1:
        frame = None
        oldtime = thistime
        thistime = time()
        try:
          frame = requests.get(self.dbline.url_img, timeout=60).content
          frame = c_convert(frame, typein=1, typeout=3)
        except requests.exceptions.ReadTimeout:
          self.logger.warning('Cam #' + str(self.id)
            + ' had timeout while getting JPG')
        except requests.exceptions.ConnectTimeout:
          self.logger.warning('Cam #' + str(self.id)
            + ' had timeout while connecting for JPG')
        except requests.exceptions.ConnectionError:
          self.logger.warning('Cam #' + str(self.id)
            + ' could not connect for getting JPG')
          sleep(60)
        if frame is not None:
          break
      elif self.dbline.cam_feed_type in {2, 3}: 
        if self.ff_proc is None:
          return(None)
        in_bytes = self.ff_proc.stdout.read(self.bytes_per_frame)
        if in_bytes:
          self.framewait = 0.0
          nptemp = np.frombuffer(in_bytes, np.uint8)
          frame = nptemp.reshape(self.dbline.cam_yres,
            self.dbline.cam_xres, 3)
          self.getting_newprozess = False
        else:
          if self.framewait < 10.0:
            self.framewait += 0.1
          sleep(self.framewait)
          frame = None
        break
    if self.dbline.cam_checkdoubles:
      imagesum = np.sum(frame)
      if self.imagecheck == imagesum:
        frame = None
      else:
        self.imagecheck = imagesum
    if frame is None:
      return(None)
    self.wd_ts = thistime
    fps = self.som.gettime()
    if fps:
      self.dbline.cam_fpsactual = fps
      mystreamline = stream.objects.filter(id = self.dbline.id)
      while True:
        try:
          mystreamline.update(cam_fpsactual = fps)
          break
        except OperationalError:
          connection.close()
      self.redis.fps_to_dev('C', self.dbline.id, fps)
    if self.dbline.cam_apply_mask and (self.viewer.drawpad.mask is not None):
      frame = cv.bitwise_and(frame, self.viewer.drawpad.mask)
    return((3, frame, thistime))

  def runner(self):
    try:
      super().runner()
      self.logname = 'camera #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      log_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Cam #'+str(self.dbline.id))
      self.wd_ts = time()
      self.wd_proc = MultiTimer(interval=10, function=self.watchdog, 
        runonstart=False)
      self.wd_proc.start()
      self.mp4_proc = MultiTimer(interval=1, function=self.checkmp4, 
        runonstart=False)
      self.mp4_proc.start()
      self.imagecheck = 0
      self.online = False
      maxcounter = 0
      while self.do_run:
        self.try_connect(maxcounter)
        if self.online:
          maxcounter = 0
          break
        else:
          if maxcounter < 300:
            maxcounter += 1
          counter = maxcounter
          while self.do_run and (counter > 0):
            counter -= 1
            sleep(djconf.getconfigfloat('long_brake', 1.0))
      self.mydetector.getviewer()
      while self.do_run:
        frameline = self.run_one()
        if frameline is not None:
          if (self.dbline.cam_view 
              and self.redis.view_from_dev('C', self.dbline.id)):
            self.viewer.inqueue.put(frameline)
          if (self.dbline.det_mode_flag 
              and (self.redis.view_from_dev('D', self.dbline.id) 
              or self.redis.data_from_dev('D', self.dbline.id))):
            self.mydetector.dataqueue.put(frameline)
          if (self.dbline.eve_mode_flag 
              and self.redis.view_from_dev('E', self.dbline.id)): 
            self.mydetector.myeventer.dataqueue.put(frameline)
      self.finished = True
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()
    self.logger.info('Finished Process '+self.logname+'...')
    self.logger.handlers.clear()
    self.stopprocess()
    if self.wd_proc is not None:
      self.wd_proc.stop()
      self.wd_proc.join()
    if self.mp4_proc is not None:
      self.mp4_proc.stop()
      self.mp4_proc.join()

  def try_connect(self, maxcounter):
    self.logger.info('[' + str(maxcounter) + '] Probing camera #' 
      + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
    if self.dbline.cam_feed_type == 1:
      self.online = False
      try:
        frame = Image.open(requests.get(self.dbline.cam_url, 
          stream=True).raw).convert('RGB') 
        frame = cv.cvtColor(np.array(frame), cv.COLOR_RGB2BGR)
        self.redis.x_y_res_to_cam(self.dbline.id, frame.shape[1], 
          frame.shape[0])
        self.dbline.xres = frame.shape[1]
        self.dbline.yres = frame.shape[0]
        self.dbline.save(update_fields=['xres', 'yres'])
        self.online = True
      except requests.exceptions.ReadTimeout:
        mylogger.warning('Cam #' + str(self.dbline.id)
          + ' had timeout while getting JPG')
      except requests.exceptions.ConnectTimeout:
        mylogger.warning('Cam #' + str(self.dbline.id)
          + ' had timeout while connecting for JPG')
      except requests.exceptions.ConnectionError:
        mylogger.warning('Cam #' + str(self.dbline.id)
          + ' could not connect for getting JPG')
    elif self.dbline.cam_feed_type in {2, 3}:
      if self.dbline.cam_repeater > 0:
        while not (self.dbline.cam_repeater in repeaterConsumer.register):
          self.logger.info('Waiting for repeater '
            + str(self.dbline.cam_repeater) + ' to register...')
          sleep(10)
        self.repeater = (
          repeaterConsumer.register[self.dbline.cam_repeater]['myself'])
        while not (self.repeater.host_register_complete):
          self.logger.info('Waiting for repeater '
            + str(self.dbline.cam_repeater) + ' to collect host list...')
          sleep(10)
        self.repeater_running = True
        try:
          probe = loads(self.repeater.probe(self.params['url_vid']))
          self.online = True
        except json.decoder.JSONDecodeError:
          self.online = False
      else:
        if self.dbline.cam_feed_type == 2:
          cmds = ['ffprobe', '-v', 'fatal', '-print_format', 'json', 
            '-show_streams', self.dbline.cam_url]
        else:
          cmds = ['ffprobe', '-v', 'fatal', '-print_format', 'json', 
            '-rtsp_transport', 'tcp', '-show_streams', self.dbline.cam_url]
        p = Popen(cmds, stdout=PIPE)
        output, _ = p.communicate()
        probe = json.loads(output)
        #print('***', probe, '***')
        self.online = (len(probe) > 0)
    if self.online:
      if self.dbline.cam_video_codec == -1:
        self.video_codec = 0
        while probe['streams'][self.video_codec]['codec_type'] != 'video':
          self.video_codec += 1
      else:
        self.video_codec = self.dbline.cam_video_codec
      self.video_codec_name = probe['streams'][self.video_codec]['codec_name']
      self.cam_fps = probe['streams'][self.video_codec]['avg_frame_rate'].split(
        '/')
      self.cam_fps = float(self.cam_fps[0]) / float(self.cam_fps[1])
      self.logger.info('Video codec: ' + self.video_codec_name + ' / ' 
        + str(self.cam_fps) + 'fps')
      self.redis.x_y_res_to_cam(
        self.dbline.id, probe['streams'][self.video_codec]['width'], 
        probe['streams'][self.video_codec]['height'])
      self.dbline.cam_xres = probe['streams'][self.video_codec]['width']
      self.dbline.cam_yres = probe['streams'][self.video_codec]['height']
      if self.dbline.cam_audio_codec == -1:
        self.audio_codec = 0
        try:
          while probe['streams'][self.audio_codec]['codec_type'] != 'audio':
            self.audio_codec  += 1
          self.audio_codec_name=probe['streams'][self.audio_codec]['codec_name']
        except IndexError:
          self.audio_codec = -1
          self.audio_codec_name = 'none'
      else:
        self.audio_codec = self.dbline.cam_audio_codec
      self.logger.info('Audio codec: ' + self.audio_codec_name)
      while True:
        try:
          self.dbline.save(update_fields=['cam_xres', 'cam_yres'])
          break
        except OperationalError:
          connection.close()
      self.bytes_per_frame = self.dbline.cam_xres * self.dbline.cam_yres * 3

  def checkmp4(self):
    try:
      if self.cam_recording:
        if path.exists(self.vid_file_path(self.vid_count + 1)):
          timestamp = time()
          targetname = self.ts_targetname(timestamp)
          try:
            move(self.vid_file_path(self.vid_count), 
              self.recordingspath + '/' + targetname)
            self.mydetector.myeventer.inqueue.put(('new_video', self.vid_count, 
              targetname, timestamp))
            self.vid_count += 1
          except FileNotFoundError:
            self.logger.warning(
                'Move did not find: '+self.vid_file_path(self.vid_count))
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def watchdog(self):
    try:
      timediff = time() - self.wd_ts
      if timediff <= 60:
        return()
      if not self.cam_active:
        return()
      if (timediff <= 180) and (self.getting_newprozess):
        return()
      if not (self.redis.view_from_dev('C', self.dbline.id)
          or self.redis.data_from_dev('C', self.dbline.id)):
        return()
      if (self.dbline.cam_repeater > 0):
        if not self.repeater_running:
          return()
        if not self.repeater.host_register_complete:
          self.online = False
          while not self.online:
            self.set_x_y(self.logger)
            if not self.online:
              sleep(60)
      self.wd_ts = time()
      self.logger.info('*** Wakeup for Camera #'
        + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
      self.stopprocess()
      self.newprocess() 
      self.getting_newprozess = True
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def newprocess(self):
    if self.dbline.cam_fpslimit:
      frame_rate = min(self.dbline.cam_fpslimit, self.cam_fps)
    else:
      frame_rate = self.cam_fps
    self.wd_ts = time()
    for f in glob(self.recordingspath + 'C' + str(self.dbline.id).zfill(4) 
        + '_????????.mp4'):
      try:
        remove(f)
      except:
        self.logger.error(format_exc())
        self.logger.handlers.clear()
        #self.logger.warning('Cam-Task failed to delete: '+f)
    if self.dbline.cam_feed_type in {2, 3}:
      if self.dbline.cam_repeater > 0:
        self.rep_cam_nr = self.repeater.get_rep_cam_nr()
        source_string = ('c_client/fifo/rep_fifo_'
          + str(self.dbline.cam_repeater) + '_' + str(self.rep_cam_nr))
      else:
        source_string = self.dbline.cam_url
      if self.redis.record_from_dev(self.type, self.dbline.id):
        self.vid_count = 0
        filepath = (self.recordingspath + 'C' 
          + str(self.dbline.id).zfill(4) + '_%08d.mp4')
      else:
        filepath = None
      outparams1 = ' -f rawvideo'
      outparams1 += ' -pix_fmt bgr24'
      outparams1 += ' -r ' + str(frame_rate)
      outparams1 += ' -vsync cfr'
      outparams1 += ' pipe:1'
      inparams = ' -i "' + source_string + '"'
      if self.video_codec_name == 'h264':
        generalparams = ' -v fatal'
        if filepath:
          outparams2 = ' -c copy'
          outparams2 += ' -segment_time ' + str(self.dbline.cam_ffmpeg_segment)
          outparams2 += ' -f segment'
          outparams2 += ' -reset_timestamps 1'
          outparams2 += ' ' + filepath
        else:
          outparams2 =''
      else:
        generalparams = ' -v fatal'
        generalparams += ' -use_wallclock_as_timestamps 1'
        if filepath:
          outparams2 = ' -c libx264'
          if self.dbline.cam_ffmpeg_fps:
            outparams2 += ' -r ' + str(self.dbline.cam_ffmpeg_fps)
          outparams2 += ' -segment_time ' + str(self.dbline.cam_ffmpeg_segment)
          outparams2 += ' -f segment'
          outparams2 += ' -reset_timestamps 1'
          if self.dbline.cam_ffmpeg_crf:
            outparams2 += ' -crf ' + str(self.dbline.cam_ffmpeg_crf)
          outparams2 += ' ' + filepath
        else:
          outparams2 = ''
      cmd = ('/usr/bin/ffmpeg ' + generalparams + inparams + outparams1 + outparams2)
      self.ff_proc = Popen(cmd, stdout=PIPE, shell=True)
      if self.dbline.cam_repeater > 0:
        self.repeater.rep_connect(self.dbline.cam_url, self.rep_cam_nr)

  def stopprocess(self):
    if self.ff_proc is not None:
      #self.ff_proc.send_signal(signal.SIGINT)
      p = Process(self.ff_proc.pid)
      child_pid = p.children(recursive=True)
      for pid in child_pid:
        oskill(pid.pid, SIGKILL)
      oskill(self.ff_proc.pid, SIGKILL)
      self.ff_proc.wait()
      self.ff_proc = None

  def ts_targetname(self, ts):
    return('C'+str(self.dbline.id).zfill(4)+'_'
      +ts2filename(ts, noblank= True)+'.mp4')

  def vid_file_path(self, nr):
    return(self.recordingspath + 'C'+str(self.dbline.id).zfill(4)
      + '_' + str(nr).zfill(8) + '.mp4')

  def reset_cam(self):
    self.logger.info('Cam #'+str(self.dbline.id)+' is off')
    if self.ff_proc is not None:
      self.ff_proc.send_signal(signal.CTRL_C_EVENT)
      self.ff_proc.wait()
      self.ff_proc = None
    self.dbline.refresh_from_db()
    self.newprocess() 
    self.logger.info('Cam #'+str(self.dbline.id)+' is on')

  def stop(self):
    super().stop()
    self.run_process.join()
    
