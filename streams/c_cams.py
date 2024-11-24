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

import cv2 as cv
import numpy as np
from select import select
from psutil import Process
from signal import SIGKILL, SIGTERM
from os import remove, path, makedirs
from shutil import move
from time import sleep, time
from setproctitle import setproctitle
from logging import getLogger
from multitimer import MultiTimer
from traceback import format_exc
from glob import glob
from subprocess import Popen, PIPE
from django.db import connection
from django.db.utils import OperationalError
from tools.c_logger import log_ini
from tools.l_tools import djconf, ts2filename
from viewers.c_viewers import c_viewer
from .c_devices import c_device
from .models import stream
from .c_camera import c_camera, logger_init

datapath = djconf.getconfig('datapath', 'data/')
virt_cam_path = djconf.getconfig('virt_cam_path', datapath + 'virt_cam_path/')

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
    self.do_run = True
    self.finished = False
    self.framewait = 0.0
    if self.dbline.cam_view:
      self.viewer = c_viewer(self, self.logger)
    self.mycam = None
    if self.dbline.cam_virtual_fps:
      self.virt_ts = 0.0
      self.virt_step = 1.0 / self.dbline.cam_virtual_fps
      self.file_over = False
      self.file_end = False
    else:
      self.mp4_proc = None
      datapath = djconf.getconfig('datapath', 'data/')
      self.recordingspath = djconf.getconfig('recordingspath', datapath + 'recordings/')
      self.checkmp4busy = False
      self.cam_fps = 0.0
      self.video_codec = -1
      self.video_codec_name = '?'
      self.audio_codec = -1
      self.vid_count = None
      if not path.exists(self.recordingspath):
        makedirs(self.recordingspath)
      for f in glob(self.recordingspath + 'C' + str(self.dbline.id).zfill(4) 
          + '_????????.mp4'):
        try:
          remove(f)
        except:
          self.logger.warning('Cam-Task failed to delete: '+f)

  def in_queue_handler(self, received):
    try:
      if super().in_queue_handler(received):
        return(True)
      else:
        #print(received)
        if (received[0] == 'reset_cam'):
          self.reset_cam()
        elif (received[0] == 'pause'):
          self.dbline.cam_pause = received[1]
        elif (received[0] == 'ptz_mdown'):
          self.mousex = received[1]
          self.mousey = received[2]
        elif (received[0] == 'ptz_mup'):
          ptz_pos = self.mycam.myptz.abs_pos
          xdiff = 0 - round((received[1] - self.mousex) / 3.0)
          ydiff = 0 - round((received[2] - self.mousey) / 3.0)
          self.mycam.myptz.goto_rel(xin=xdiff, yin=ydiff)
        elif (received[0] == 'ptz_zoom'):
          self.mycam.myptz.goto_rel(zin= 0-received[1])
        elif (received[0] == 'zoom_abs'):
          self.mycam.myptz.goto_abs(z = received[1])
        elif (received[0] == 'pos_rel'):
          xdiff = 0 - received[1]
          ydiff = 0 - received[2]
          self.mycam.myptz.goto_rel(xin=xdiff, yin=ydiff)
        else:
          return(False)
        return(True)
    except:
      self.logger.error('Error in process: ' + self.logname + ' (in_queue_handler)')
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def run_one(self):
    if not self.do_run:
      return(None)
    if self.dbline.cam_virtual_fps:
      self.virt_ts += self.virt_step
      self.redis.set_virt_time(self.id, self.virt_ts)
      in_ts = self.virt_ts
    else:
      in_ts = time()
    while True:
      if (self.redis.check_if_counts_zero('C', self.dbline.id) 
          or self.dbline.cam_pause):
        if self.cam_active:
          if self.cam_ts is None:
            self.cam_ts = time()
            break
          else:
            if ((time() - self.cam_ts) > 60) or self.dbline.cam_pause:
              self.logger.info('Cam #'+str(self.dbline.id)+' is off')
              self.cam_active = False
              self.cam_ts = None
              self.stopprocess()
            else:
              break
        else:
          if not self.do_run:
            return(None)
          sleep(djconf.getconfigfloat('short_brake', 0.01))
      else:
        if self.cam_active:
          if (not self.redis.record_from_dev('C', self.dbline.id)
              and self.cam_recording):
            if self.ffmpeg_recording:
              self.stopprocess()
              self.newprocess() 
            self.cam_recording = False
            self.logger.info('Cam #'+str(self.dbline.id)+' stopped recording')
          if (self.redis.record_from_dev('C', self.dbline.id) 
              and not self.cam_recording):
            if not self.ffmpeg_recording:
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
    while True:
      if self.ff_proc is None:
        return(None)
      ready_to_read, _, _ = select([self.ff_proc.stdout], [], [], 5.0) 
      if ready_to_read:
        try:
          in_bytes = self.ff_proc.stdout.read(self.bytes_per_frame)
        except  AttributeError: 
          in_bytes = None
      else:
        in_bytes = None
      if in_bytes:
        self.framewait = 0.0
        nptemp = np.frombuffer(in_bytes, np.uint8)
        try:
          frame = nptemp.reshape(self.dbline.cam_yres,
            self.dbline.cam_xres, 3)
        except ValueError:
          self.logger.warning('ValueError: cannot reshape array of size ' 
            + str(nptemp.size) + ' into shape ' 
            + str((self.dbline.cam_yres, self.dbline.cam_xres, 3)))
          return(None)
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
    self.wd_ts = in_ts
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
    if self.dbline.cam_virtual_fps and self.file_end:
      in_ts = 0.0
      self.file_end = False  
    return((3, frame, in_ts))

  def runner(self):
    try:
      super().runner()
      self.logname = 'camera #'+str(self.dbline.id)
      self.logger = getLogger(self.logname)
      log_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Cam #'+str(self.dbline.id))
      logger_init(self.logger)
      if self.dbline.cam_virtual_fps:
        self.wd_ts = 0.0
        wd_interval = 1.0
      else:
        self.mycam = c_camera(
          self.id,
          control_mode = self.dbline.cam_control_mode,
          control_ip=self.dbline.cam_control_ip, 
          control_port=self.dbline.cam_control_port, 
          control_user=self.dbline.cam_control_user, 
          control_pass=self.dbline.cam_control_passwd, 
          url=self.dbline.cam_url.replace('{address}', self.dbline.cam_control_ip)
        )
        self.mp4timestamp = 0.0
        self.wd_ts = time()
        wd_interval = 10.0
      self.wd_proc = MultiTimer(interval=wd_interval, function=self.watchdog, 
        runonstart=False)
      self.wd_proc.start()
      if not self.dbline.cam_virtual_fps:
        self.mp4_proc = MultiTimer(interval=1, function=self.checkmp4, 
          runonstart=False)
        self.mp4_proc.start()
      self.imagecheck = 0
      self.online = False
      if self.dbline.cam_virtual_fps:
        self.online = True
        self.bytes_per_frame = self.dbline.cam_xres * self.dbline.cam_yres * 3
      else:
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
              and (not self.redis.check_if_counts_zero('E', self.dbline.id))): 
            self.mydetector.myeventer.dataqueue.put(frameline)
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
      self.logger.handlers.clear()
      self.stopprocess()
      if self.wd_proc is not None:
        self.wd_proc.stop()
        self.wd_proc.join()
      if not self.dbline.cam_virtual_fps:
        if self.mp4_proc is not None:
          self.mp4_proc.stop()
          self.mp4_proc.join()
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def try_connect(self, maxcounter):
    if self.dbline.cam_pause:
      return()
    self.logger.info('[' + str(maxcounter) + '] Probing camera #' 
      + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
    self.mycam.ffprobe()
    probe = self.mycam.probe
    #print('***', probe, '***')
    self.online = self.mycam.online
    if self.online:
      if self.dbline.cam_video_codec == -1:
        self.video_codec = 0
        while probe['streams'][self.video_codec]['codec_type'] != 'video':
          self.video_codec += 1
      else:
        self.video_codec = self.dbline.cam_video_codec
      self.video_codec_name = probe['streams'][self.video_codec]['codec_name']
      self.cam_fps = (
        probe['streams'][self.video_codec]['r_frame_rate'].split('/'))
      try:
        self.cam_fps = float(self.cam_fps[0]) / float(self.cam_fps[1])
      except ZeroDivisionError:
        self.cam_fps = 0.0 
      self.real_fps = (
        probe['streams'][self.video_codec]['avg_frame_rate'].split('/'))
      if (self.real_fps[0] == '0') or (self.real_fps[1] == '0'):
        self.real_fps = 0.0
      else:
        self.real_fps = float(self.real_fps[0]) / float(self.real_fps[1])
      self.logger.info('+++++ CAM #' + str(self.dbline.id) + ': ' + self.dbline.name)
      self.logger.info('+++++ Video codec: ' + self.video_codec_name + ' / Cam: ' + str(self.cam_fps) + 'fps / Connect: ' + str(self.real_fps) + 'fps')
      try:
        self.redis.x_y_res_to_cam(
          self.dbline.id, probe['streams'][self.video_codec]['width'], 
          probe['streams'][self.video_codec]['height'])
      except KeyError:
        self.logger.warning('Key Error in redis.x_y_res_to_cam')
        self.online = False
        return()    
      self.dbline.cam_xres = probe['streams'][self.video_codec]['width']
      self.dbline.cam_yres = probe['streams'][self.video_codec]['height']
      while True:
        try:
          self.dbline.save(update_fields=['cam_xres', 'cam_yres'])
          break
        except OperationalError:
          connection.close()
      if self.dbline.cam_audio_codec == -1:
        self.audio_codec = 0
        try:
          while probe['streams'][self.audio_codec]['codec_type'] != 'audio':
            self.audio_codec  += 1
          self.audio_codec_name=probe['streams'][self.audio_codec]['codec_name']
        except IndexError:
          self.audio_codec = -1
      else:
        self.audio_codec = self.dbline.cam_audio_codec
      if self.audio_codec >= 0: 
        self.audio_codec_name = probe['streams'][self.audio_codec]['codec_name']
      else:  
        self.audio_codec_name = 'none'
      self.logger.info('+++++ Audio codec: ' + self.audio_codec_name)
      while True:
        try:
          self.dbline.save(update_fields=['cam_xres', 'cam_yres'])
          break
        except OperationalError:
          connection.close()
      self.bytes_per_frame = self.dbline.cam_xres * self.dbline.cam_yres * 3

  def checkmp4(self):
    try:
      if self.checkmp4busy:
        return()
      self.checkmp4busy = True
      if self.cam_recording:
        if self.vid_count is None:
          self.checkmp4busy = False
          return()
        if path.exists(self.vid_file_path(self.vid_count + 2)):
          try:
            timestamp = path.getmtime(self.vid_file_path(self.vid_count))
          except FileNotFoundError:
            self.checkmp4busy = False
            return()
          if timestamp > self.mp4timestamp:
            self.mp4timestamp = timestamp
          else:
            return()
          targetname = self.ts_targetname(timestamp)
          try:
            move(self.vid_file_path(self.vid_count), 
              self.recordingspath + '/' + targetname)
            self.mydetector.myeventer.inqueue.put(('new_video', self.vid_count, 
              targetname, timestamp))
            #self.logger.info('CAM sent: ' + str(('new_video', self.vid_count, 
            #  targetname, timestamp)))
            self.vid_count += 1
          except FileNotFoundError:
            self.logger.warning(
                'Move did not find: '+self.vid_file_path(self.vid_count))
      self.checkmp4busy = False
    except:
      self.checkmp4busy = False
      self.logger.error('Error in process: ' + self.logname + ' (checkmp4)')
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def watchdog(self):
    try:
      if self.dbline.cam_virtual_fps:
        if self.ff_proc is None or self.ff_proc.poll() is None:
          return()
        else:
          self.file_end = True  
      else:
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
        self.wd_ts = time()
      if self.dbline.cam_virtual_fps:
        self.logger.info('*** Restarting Video, VirtCam #'
          + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
      else:
        self.logger.info('*** Wakeup for Camera #'
          + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
      if not self.dbline.cam_virtual_fps:
        self.stopprocess()
      self.newprocess() 
      self.getting_newprozess = True
    except:
      self.logger.error('Error in process: ' + self.logname + ' (watchdog)')
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def newprocess(self):
    if (not self.dbline.cam_virtual_fps 
        and self.dbline.cam_fpslimit 
        and self.dbline.cam_fpslimit < self.cam_fps):
      det_frame_rate = min(self.dbline.cam_fpslimit, self.cam_fps)
    else:
      det_frame_rate = 0.0
    self.wd_ts = time()
    if self.dbline.cam_virtual_fps:
      source_string = virt_cam_path + self.dbline.cam_url
      filepath = None
    else:
      self.mydetector.myeventer.inqueue.put(('purge_videos', ))
      source_string = self.dbline.cam_url.replace('{address}', self.dbline.cam_control_ip)
      if self.redis.record_from_dev(self.type, self.dbline.id):
        self.vid_count = 0
        filepath = (self.recordingspath + 'C' 
          + str(self.dbline.id).zfill(4) + '_%08d.mp4')
      else:
        filepath = None
    outparams1 = ''  
    if not self.dbline.cam_virtual_fps:
      outparams1 += ' -map 0:'+str(self.video_codec) + ' -map -0:a'
    outparams1 += ' -f rawvideo'
    outparams1 += ' -pix_fmt bgr24'
    if det_frame_rate:
      outparams1 += ' -r ' + str(det_frame_rate)
    if not self.dbline.cam_virtual_fps:
      outparams1 += ' -fps_mode cfr'
    outparams1 += ' pipe:1'
    inparams = ' -i "' + source_string + '"'
    generalparams = ' -v fatal'
    if not self.dbline.cam_virtual_fps:
      if source_string[:4].upper() == 'RTSP':
        generalparams += ' -rtsp_transport tcp'
      if self.dbline.cam_red_lat:
        generalparams += ' -fflags nobuffer'
        generalparams += ' -flags low_delay'
      if self.video_codec_name not in {'h264', 'hevc'}:
        generalparams += ' -use_wallclock_as_timestamps 1'
    outparams2 = ''
    if filepath:
      self.ffmpeg_recording = True
      if self.dbline.cam_ffmpeg_fps and self.dbline.cam_ffmpeg_fps < self.cam_fps:
        video_framerate = self.dbline.cam_ffmpeg_fps
      else:
        video_framerate = None
      outparams2 += ' -map 0:'+str(self.video_codec)
      if self.audio_codec > -1:
        outparams2 += ' -map 0:'+str(self.audio_codec)
      if self.video_codec_name in {'h264', 'hevc'}:
        if video_framerate:
          outparams2 += ' -c:v libx264'
        else:
          outparams2 += ' -c:v copy'
        if self.audio_codec_name == 'pcm_alaw':
          outparams2 += ' -c:a aac'
        else:
          outparams2 += ' -c:a copy'
      else:    
        outparams2 = ' -c libx264'
      if video_framerate:
        outparams2 += ' -r ' + str(video_framerate)
        outparams2 += ' -g ' + str(round(video_framerate * self.dbline.cam_ffmpeg_segment))
      outparams2 += ' -f segment'
      outparams2 += ' -segment_time ' + str(self.dbline.cam_ffmpeg_segment)
      if video_framerate:
        outparams2 += ' -segment_time_delta '+str(0.5 / (video_framerate))
      outparams2 += ' -reset_timestamps 1'
      if self.dbline.cam_ffmpeg_crf:
        outparams2 += ' -crf ' + str(self.dbline.cam_ffmpeg_crf)
      outparams2 += ' ' + filepath
    else:
      self.ffmpeg_recording = True  
    cmd = ('/usr/bin/ffmpeg ' + generalparams + inparams + outparams1 
      + outparams2)
    #self.logger.info('#####' + cmd)
    self.ff_proc = Popen(cmd, stdout=PIPE, shell=True)

  def stopprocess(self):
    if self.ff_proc is not None:
      p = Process(self.ff_proc.pid)
      child_pid = p.children(recursive=True)
      for pid in child_pid:
        pid.send_signal(SIGKILL)
        pid.wait()
      self.ff_proc.send_signal(SIGKILL)
      self.ff_proc.wait()
      self.ff_proc = None

  def ts_targetname(self, ts):
    return('C'+str(self.dbline.id).zfill(4)+'_'
      +ts2filename(ts, noblank= True)+'.mp4')

  def vid_file_path(self, nr):
    return(self.recordingspath + 'C'+str(self.dbline.id).zfill(4)
      + '_' + str(nr).zfill(8) + '.mp4')

  def reset_cam(self):
    if not self.cam_active:
      return()
    self.logger.info('Cam #'+str(self.dbline.id)+' is off')
    if self.ff_proc is not None:
      self.ff_proc.send_signal(SIGTERM)
      self.ff_proc.wait()
      self.ff_proc = None
    while True:
      try:
        self.dbline.refresh_from_db()
        break
      except OperationalError:
        connection.close()
    self.newprocess() 
    self.logger.info('Cam #'+str(self.dbline.id)+' is on')

  def set_pause(self, status):
    self.inqueue.put(('pause', status))
    
