"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
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
import aiofiles.os
import aioshutil
import os
import cv2 as cv
import numpy as np
from aiopath import AsyncPath
from psutil import Process
from signal import SIGKILL, SIGTERM
from setproctitle import setproctitle
from logging import getLogger
from traceback import format_exc
from time import time
from globals.c_globals import viewers
from tools.c_spawn import viewable
from tools.l_break import a_break_time, a_break_type, BR_MEDIUM, BR_LONG
from .redis import my_redis as streams_redis
from .c_camera import c_camera

from multiprocessing import SimpleQueue

class c_cam(viewable):
  def __init__(self, dbline, detector_dataq, eventer_dataq, eventer_inq, logger, ):
    self.type = 'C'
    self.dbline = dbline
    self.id = dbline.id
    self.detector_dataq = detector_dataq
    self.eventer_dataq = eventer_dataq
    self.eventer_inq = eventer_inq
    self.mycam = None
    super().__init__(logger, )

  async def async_runner(self):
    import django
    django.setup()
    from tools.c_logger import alog_ini
    from tools.l_tools import djconf
    try:
      self.logname = 'camera #' + str(self.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Camera #'+str(self.id))
      if self.dbline.cam_virtual_fps:
        self.wd_ts = 0.0
        self.wd_interval = 1.0
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
        self.wd_interval = 10.0 
      await super().async_runner() 
      self.viewer.drawpad.mask = None
      self.mode_flag = self.dbline.cam_mode_flag
      self.cam_active = False
      self.cam_recording = False
      self.ff_proc = None
      self.getting_newprozess = False
      self.wd_proc = None
      self.finished = False
      self.framewait = 0.0
      datapath = await djconf.agetconfig('datapath', 'data/')
      if self.dbline.cam_virtual_fps:
        self.virt_cam_path = await djconf.agetconfig(
          'virt_cam_path', 
          datapath + 'virt_cam_path/', 
        )
        self.virt_ts = 0.0
        self.virt_step = 1.0 / self.dbline.cam_virtual_fps
        self.file_over = False
        self.file_end = False
      else:
        self.mp4_proc = None
        datapath = await djconf.agetconfig('datapath', 'data/')
        self.recordingspath = await djconf.agetconfig(
          'recordingspath', 
          datapath + 'recordings/', 
        )
        self.checkmp4busy = False
        self.cam_fps = 0.0
        self.video_codec = -1
        self.video_codec_name = '?'
        self.audio_codec = -1
        self.vid_count = None
        if not await aiofiles.os.path.exists(self.recordingspath):
          await aiofiles.os.makedirs(self.recordingspath)
        path = AsyncPath(self.recordingspath)
        async for file in path.glob(f'C{str(self.dbline.id).zfill(4)}_????????.mp4'):
          try:
            await asyncio.to_thread(os.remove, file),
          except:
            self.logger.warning('Cam-Task failed to delete: ' + file)
      self.wd_proc = asyncio.create_task(self.watchdog())
      if not self.dbline.cam_virtual_fps:
        self.mp4_proc = asyncio.create_task(self.checkmp4())
      self.imagecheck = 0
      self.online = False
      if self.dbline.cam_virtual_fps:
        self.online = True
        self.bytes_per_frame = self.dbline.cam_xres * self.dbline.cam_yres * 3
      else:
        maxcounter = 0
        while self.do_run:
          await self.try_connect(maxcounter)
          if self.online:
            maxcounter = 0
            break
          else:
            if maxcounter < 300:
              maxcounter += 1
            counter = maxcounter
            while self.do_run and (counter > 0):
              counter -= 1
              await a_break_type(BR_LONG)
      print('Launch: cam')
      while self.do_run:
        frameline = await self.run_one()
        if frameline is not None:
          if (self.dbline.cam_view 
              and streams_redis.view_from_dev('C', self.id)):
            await self.viewer_queue.put(frameline)
          if (self.dbline.det_mode_flag 
              and (streams_redis.view_from_dev('D', self.dbline.id) 
              or streams_redis.data_from_dev('D', self.dbline.id))): 
            await self.detector_dataq.put(frameline) 
          if (self.dbline.eve_mode_flag 
              and (not streams_redis.check_if_counts_zero('E', self.dbline.id))):
            await self.eventer_dataq.put(frameline)
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
      await self.stopprocess()
      if self.wd_proc is not None:
        self.wd_proc.cancel()
        try:
          await self.wd_proc  # Warten auf die Beendigung
        except asyncio.CancelledError:
          self.logger.info("Watchdog-Task wurde erfolgreich beendet.")
      if not self.dbline.cam_virtual_fps:
        if self.mp4_proc is not None:
          self.mp4_proc.cancel()
        try:
          await self.wd_proc  # Warten auf die Beendigung
        except asyncio.CancelledError:
          self.logger.info("MP4-Task wurde erfolgreich beendet.")
    except:
      self.logger.error('Error in process: ' + self.logname)
      self.logger.error(format_exc())
    
  async def process_received(self, received):  
    result = True
    if (received[0] == 'set_mask'):
      self.viewer.drawpad.ringlist = received[1]
      self.viewer.drawpad.make_screen()
      self.viewer.drawpad.mask_from_polygons()
    elif (received[0] == 'set_apply_mask'):
      self.dbline.cam_apply_mask = received[1]
    elif (received[0] == 'reset_cam'):
      await self.reset_cam()
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
      self.mycam.myptz.goto_rel(zian= 0-received[1])
    elif (received[0] == 'zoom_abs'):
      self.mycam.myptz.goto_abs(z = received[1])
    elif (received[0] == 'pos_rel'):
      xdiff = 0 - received[1]
      ydiff = 0 - received[2]
      self.mycam.myptz.goto_rel(xin=xdiff, yin=ydiff)
    else:
      result = False  
    return(result)
      
  async def run_one(self):
    if not self.do_run:
      return(None)     
    if self.dbline.cam_virtual_fps:
      self.virt_ts += self.virt_step
      streams_redis.set_virt_time(self.id, self.virt_ts)
      in_ts = self.virt_ts
    else:
      in_ts = time() 
    while True:
      if (streams_redis.check_if_counts_zero('C', self.dbline.id) 
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
              await self.stopprocess()
            else:
              break
        else:
          if not self.do_run:
            return(None)
      else:
        if self.cam_active:
          if (not streams_redis.record_from_dev('C', self.dbline.id)
              and self.cam_recording):
            if self.ffmpeg_recording:
              await self.stopprocess()
              await self.newprocess() 
            self.cam_recording = False
            self.logger.info('Cam #'+str(self.dbline.id)+' stopped recording')
          if (streams_redis.record_from_dev('C', self.dbline.id) 
              and not self.cam_recording):
            if not self.ffmpeg_recording:
              await self.stopprocess()
              await self.newprocess() 
            self.cam_recording = True
            self.logger.info('Cam #'+str(self.dbline.id)+' started recording')
        else:
          await self.newprocess() 
          self.logger.info('Cam #'+str(self.dbline.id)+' is on')
          self.cam_active = True
        self.cam_ts = None
        break
    while True:
      if self.ff_proc is None:
        return(None)
      in_bytes = bytearray()
      bytes_needed = self.bytes_per_frame
      while bytes_needed > 0:
        try:
          chunk = await asyncio.wait_for(self.ff_proc.stdout.read(min(65536, bytes_needed)), timeout=5.0)
          if not chunk:
            in_bytes = None
            break
          in_bytes.extend(chunk)
          bytes_needed -= len(chunk)
        except asyncio.TimeoutError:
          in_bytes = None
          break
        except AttributeError:
          in_bytes = None
          break
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
        await a_break_time(self.framewait)
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
      await self.dbline.asave(update_fields = ['cam_fpsactual', ])
      streams_redis.fps_to_dev('C', self.dbline.id, fps)
    if self.dbline.cam_apply_mask and (self.viewer.drawpad.mask is not None):
      frame = cv.bitwise_and(frame, self.viewer.drawpad.mask)
    if self.dbline.cam_virtual_fps and self.file_end:
      in_ts = 0.0
      self.file_end = False 
    return([3, frame, in_ts])

  async def try_connect(self, maxcounter):
    if self.dbline.cam_pause:
      return()
    self.logger.info('[' + str(maxcounter) + '] Probing camera #' 
      + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
    await self.mycam.ffprobe()
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
      self.logger.info('+++++ Video codec: ' + self.video_codec_name 
        + ' / Cam: ' + str(self.cam_fps) + 'fps / Connect: ' 
        + str(self.real_fps) + 'fps')
      try:
        streams_redis.x_y_res_to_cam(
          self.dbline.id, probe['streams'][self.video_codec]['width'], 
          probe['streams'][self.video_codec]['height'])
      except KeyError:
        self.logger.warning('Key Error in redis.x_y_res_to_cam')
        self.online = False
        return()  
      self.dbline.cam_xres = probe['streams'][self.video_codec]['width']
      self.dbline.cam_yres = probe['streams'][self.video_codec]['height']
      await self.dbline.asave(update_fields=('cam_xres', 'cam_yres',))
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
      self.bytes_per_frame = self.dbline.cam_xres * self.dbline.cam_yres * 3

  async def checkmp4(self):
    try:
      while True:
        try:
          await a_break_type(BR_LONG)
        except asyncio.CancelledError:
          self.logger.info("MP4-Task wurde abgebrochen.")
          return  # Sauber beenden
        #print('MP4')
        if self.checkmp4busy:
          continue
        self.checkmp4busy = True
        if self.cam_recording:
          if self.vid_count is None:
            self.checkmp4busy = False
            continue
          if await aiofiles.os.path.exists(self.vid_file_path(self.vid_count + 2)):
            try:
              #print(self.vid_file_path(self.vid_count))
              timestamp = await asyncio.to_thread(
                os.path.getmtime, 
                self.vid_file_path(self.vid_count),
              )
            except FileNotFoundError:
              self.checkmp4busy = False
              continue
            if timestamp > self.mp4timestamp:
              self.mp4timestamp = timestamp
            else:
              continue
            targetname = self.ts_targetname(timestamp)
            try:
              await aioshutil.move(self.vid_file_path(self.vid_count), 
                self.recordingspath + '/' + targetname)
              self.mydetector.myeventer.inqueue.put(('new_video', self.vid_count, 
                targetname, timestamp))
              self.vid_count += 1
            except FileNotFoundError:
              self.logger.warning(
                  'Move did not find: '+self.vid_file_path(self.vid_count))
        self.checkmp4busy = False
    except:
      self.checkmp4busy = False
      self.logger.error('Error in process: ' + self.logname + ' (checkmp4)')
      self.logger.error(format_exc())

  async def watchdog(self):
    try:
      while True:
        try:
          await a_break_time(self.wd_interval)
        except asyncio.CancelledError:
          self.logger.info("Watchdog-Task wurde abgebrochen.")
          return  # Sauber beenden
        if self.dbline.cam_virtual_fps:
          if self.ff_proc is None or self.ff_proc.poll() is None:
            continue
          else:
            self.file_end = True  
        else:
          timediff = time() - self.wd_ts
          #print('WD', time(), self.wd_ts, timediff)
          if timediff <= 60:
            continue
          if not self.cam_active:
            self.wd_ts = time()  
            continue
          if (timediff <= 180) and (self.getting_newprozess):
            continue
          if not (streams_redis.view_from_dev('C', self.dbline.id)
              or streams_redis.data_from_dev('C', self.dbline.id)):
            continue
          self.wd_ts = time()
        if self.dbline.cam_virtual_fps:
          self.logger.info('*** Restarting Video, VirtCam #'
            + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
        else:
          self.logger.info('*** Wakeup for Camera #'
            + str(self.dbline.id) + ' (' + self.dbline.name + ')...')
        if not self.dbline.cam_virtual_fps:
          await self.stopprocess()
        await self.newprocess() 
        self.getting_newprozess = True
    except:
      self.logger.error('Error in process: ' + self.logname + ' (watchdog)')
      self.logger.error(format_exc())

  async def newprocess(self):
    from globals.c_globals import viewables
    inp_frame_rate = 0.0
    if self.dbline.cam_virtual_fps:
      if (self.dbline.cam_fpslimit 
          and self.dbline.cam_fpslimit < self.dbline.cam_virtual_fps):
        inp_frame_rate = min(self.dbline.cam_fpslimit, self.dbline.cam_virtual_fps)
    else:  
      if self.dbline.cam_fpslimit and self.dbline.cam_fpslimit < self.cam_fps:
        inp_frame_rate = min(self.dbline.cam_fpslimit, self.cam_fps)
    self.wd_ts = time()
    if self.dbline.cam_virtual_fps:
      source_string = self.virt_cam_path + self.dbline.cam_url
      filepath = None
    else:
      self.eventer_inq.put(('purge_videos', ))
      source_string = self.dbline.cam_url.replace('{address}', self.dbline.cam_control_ip)
      if streams_redis.record_from_dev(self.type, self.dbline.id):
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
    if inp_frame_rate:
      outparams1 += ' -r ' + str(inp_frame_rate)
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
        outparams2 += (' -g ' 
          + str(round(video_framerate * self.dbline.cam_ffmpeg_segment)))
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
    self.ff_proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE)

  async def stopprocess(self):
    if self.ff_proc is not None and self.ff_proc.returncode is None:
      p = Process(self.ff_proc.pid)
      child_pid = p.children(recursive=True)
      for pid in child_pid:
        pid.send_signal(SIGKILL)
        pid.wait()
      self.ff_proc.send_signal(SIGKILL)
      await self.ff_proc.wait()
      self.ff_proc = None

  def ts_targetname(self, ts):
    return('C'+str(self.dbline.id).zfill(4)+'_'
      +ts2filename(ts, noblank= True)+'.mp4')

  def vid_file_path(self, nr):
    return(self.recordingspath + 'C'+str(self.dbline.id).zfill(4)
      + '_' + str(nr).zfill(8) + '.mp4')

  async def reset_cam(self):
    if not self.cam_active:
      return()
    self.logger.info('Cam #'+str(self.dbline.id)+' is off')
    if self.ff_proc is not None:
      self.ff_proc.send_signal(SIGTERM)
      await self.ff_proc.wait()
      self.ff_proc = None
    await self.dbline.arefresh_from_db()
    await self.newprocess() 
    self.logger.info('Cam #'+str(self.dbline.id)+' is on')

  def set_pause(self, status):
    self.inqueue.put(('pause', status))
    
