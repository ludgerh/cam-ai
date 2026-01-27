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
import shlex
import asyncio
import aiofiles.os
import aioshutil
import os
import cv2 as cv
import numpy as np
import queue
import threading
from aiopath import AsyncPath
from psutil import Process, NoSuchProcess, TimeoutExpired, AccessDenied
from signal import SIGINT, SIGKILL
from setproctitle import setproctitle
from logging import getLogger
from time import time
from django.db import OperationalError
from channels.db import aclose_old_connections
from globals.c_globals import viewers
from tools.c_spawn import viewable
from tools.l_break import a_break_time, a_break_type, break_type, BR_SHORT, BR_MEDIUM, BR_LONG
from tools.l_tools import djconf, ts2filename
from tools.l_sysinfo import is_raspi
from .redis import my_redis as streams_redis
from .c_camera import c_camera

datapath = djconf.getconfig('datapath', 'data/')
logpath = djconf.getconfig('logdir', default = datapath + 'logs/')

class c_cam(viewable):
  def __init__(self, dbline, mydetector_data, myeventer_data, myeventer_in, logger, ):
    self.type = 'C'
    self.dbline = dbline
    self.id = dbline.id
    self.mydetector_data = mydetector_data
    self.myeventer_data = myeventer_data
    self.myeventer_in = myeventer_in
    self.mycam = None
    super().__init__(logger, )

  async def async_runner(self):
    try:
      import django
      django.setup()
      from tools.c_logger import alog_ini
      self.logname = 'camera #' + str(self.id)
      self.logger = getLogger(self.logname)
      await alog_ini(self.logger, self.logname)
      setproctitle('CAM-AI-Camera #'+str(self.id))
      self.fifo_path = await djconf.agetconfig('fifo_path', '/home/cam_ai/shm/fifo/')
      await aiofiles.os.makedirs(self.fifo_path, exist_ok=True)
      self.fifo_path += f'cam{self.id}.pipe'
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
      self.mode_flag = self.dbline.cam_mode_flag
      self.cam_active = False
      self.cam_recording = False
      self.ff_proc = None
      self.getting_newprozess = False
      self.wd_proc = None
      self.finished = False
      self.framewait = 0.0
      self.reset_buffer = False
      datapath = await djconf.agetconfig('datapath', 'data/')
      if self.dbline.cam_virtual_fps:
        self.virt_cam_path = await djconf.agetconfig(
          'virt_cam_path', 
          datapath + 'virt_cam_path/', 
        )
        self.virt_cam_path_ram = await djconf.agetconfig('virt_cam_path_ram', '')
        if self.virt_cam_path_ram:
          await aiofiles.os.makedirs(self.virt_cam_path_ram, exist_ok=True)
          await aioshutil.copy(
            self.virt_cam_path + self.dbline.cam_url, 
            self.virt_cam_path_ram + self.dbline.cam_url, 
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
        self._mp4_lock = asyncio.Lock()
        self.cam_fps = 0.0
        self.video_codec = -1
        self.video_codec_name = '?'
        self.audio_codec = -1
        self.vid_count = None
        await aiofiles.os.makedirs(self.recordingspath, exist_ok=True)
        path = AsyncPath(self.recordingspath)
        async for file in path.glob(f'C{str(self.id).zfill(4)}*.mp4'):
          try:
            await asyncio.to_thread(os.remove, file)
          except Exception as e:
            self.logger.warning(
              f'CA{self.id}: Cam-Task failed to delete: {file}: {e}'
            )  
      self.wd_proc = asyncio.create_task(self.watchdog(), name = 'watchdog')
      if not self.dbline.cam_virtual_fps:
        self.mp4_proc = asyncio.create_task(self.checkmp4(), name = 'checkmp4')
      self.imagecheck = 0
      self.online = False
      if self.dbline.cam_virtual_fps:
        self.online = True
        self.bytes_per_frame = self.dbline.cam_xres * self.dbline.cam_yres * 3
      else:
        maxcounter = 0
        while not self.got_sigint:
          await self.try_connect(maxcounter)
          if self.online:
            maxcounter = 0
            break
          else:
            if maxcounter < 300:
              maxcounter += 1
            counter = maxcounter
            while not self.got_sigint and counter > 0:
              counter -= 1
              await a_break_type(BR_LONG)
      if self.dbline.cam_apply_mask:
        await self.viewer.drawpad.set_mask_local()
      self.raw_queue = queue.Queue(maxsize=1)
      self.raw_running = True
      #print(f'Launch: cam#{self.id}')
      while not self.got_sigint:
        frameline = await self.run_one()
        if self.got_sigint:
          break 
        if frameline:
          if (self.dbline.cam_view 
              and streams_redis.view_from_dev('C', self.id)):
            await self.viewer_queue.put(frameline)
          if (self.dbline.det_mode_flag 
              and (streams_redis.view_from_dev('D', self.id) 
              or streams_redis.data_from_dev('D', self.id))
              and frameline):
            try:
              await asyncio.wait_for(self.mydetector_data.put(frameline), timeout=5.0)
            except asyncio.TimeoutError:
              pass
          if (self.dbline.eve_mode_flag 
              and (not streams_redis.check_if_counts_zero('E', self.id))):
            try:
              await asyncio.wait_for(self.myeventer_data.put(frameline), timeout=5.0)
            except asyncio.TimeoutError:
              pass
        else:
          await a_break_type(BR_SHORT)
      await self.dbline.asave(update_fields = ['cam_fpsactual', ])
      if getattr(self, "_inq_task", None):
        self._inq_task.cancel()
        try:
          await self._inq_task
        except asyncio.CancelledError:
          pass
      self.finished = True
      self.logger.info('Finished Process '+self.logname+'...')
      await self.stopprocess()
      if self.wd_proc is not None:
        self.wd_proc.cancel()
        try:
          await self.wd_proc
        except asyncio.CancelledError:
          pass
      if not self.dbline.cam_virtual_fps:
        if self.mp4_proc is not None:
          self.mp4_proc.cancel()
        try:
          await self.mp4_proc
        except asyncio.CancelledError:
          pass
      try:
        await asyncio.get_running_loop().shutdown_default_executor()
      except RuntimeError:
        pass
    except Exception as fatal:
      self.logger.error(
        'Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("async_runner crashed: %s", fatal, exc_info=True)
    
  async def process_received(self, received):  
    result = True
    #print(f'***** CAM Inqueue #{self.id}:', received)
    if (received[0] == 'set_mask'):
      await self.viewer.drawpad.set_mask_local(received[1])
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
    elif (received[0] == 'stop'):
      if self.dbline.cam_virtual_fps and self.virt_cam_path_ram:
        await aiofiles.os.remove(self.virt_cam_path_ram + self.dbline.cam_url)
    else:
      result = False   
    return(result)
      
  async def run_one(self):
    if self.got_sigint:
      await a_break_type(BR_LONG)
      return(None)   
    if self.dbline.cam_virtual_fps:
      self.virt_ts += self.virt_step
      streams_redis.set_virt_time(self.id, self.virt_ts)
      in_ts = self.virt_ts
    else:
      in_ts = time() 
    while True:
      if self.dbline.cam_pause or streams_redis.check_if_counts_zero('C', self.id):
        if self.cam_active:
          if self.cam_ts is None:
            self.cam_ts = time()
            break
          else:
            if ((time() - self.cam_ts) > 60) or self.dbline.cam_pause:
              self.logger.info('Cam #'+str(self.id)+' is off')
              self.cam_active = False
              self.cam_ts = None
              await self.stopprocess()
            else:
              break
        else: 
          await a_break_type(BR_LONG)
          return(None)
      else:
        if self.cam_active:
          if self.cam_recording and not streams_redis.record_from_dev('C', self.id):
            if self.ffmpeg_recording:
              await self.stopprocess()
              await self.newprocess() 
            self.cam_recording = False
            self.logger.info('Cam #'+str(self.id)+' stopped recording')
          if not self.cam_recording and streams_redis.record_from_dev('C', self.id): 
            if not self.ffmpeg_recording:
              await self.stopprocess()
              await self.newprocess() 
            self.cam_recording = True
            self.logger.info('Cam #'+str(self.id)+' started recording')
        else:
          await self.newprocess() 
          self.logger.info('Cam #'+str(self.id)+' is on')
          self.cam_active = True
        self.cam_ts = None
        break
    while True:
      if self.ff_proc is None:
        await a_break_type(BR_LONG)
        return(None)
      try:
        #in_bytes = await asyncio.to_thread(self.raw_queue.get)
        in_bytes = self.raw_queue.get_nowait()
      except queue.Empty:
        await a_break_type(BR_SHORT)
        return(None)
      if in_bytes:
        self.framewait = 0.0
        nptemp = np.frombuffer(in_bytes, np.uint8)
        try:
          frame = nptemp.reshape(self.dbline.cam_yres,
            self.dbline.cam_xres, 3)
        except ValueError:
          self.logger.warning(
            f'CA{self.id}: ValueError: cannot reshape array of size '
            + str(nptemp.size) + ' into shape ' 
            + str((self.dbline.cam_yres, self.dbline.cam_xres, 3))
          )  
          await a_break_type(BR_LONG)
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
      streams_redis.fps_to_dev('C', self.id, fps)
    if self.dbline.cam_apply_mask:
      frame = await asyncio.to_thread(cv.bitwise_and, frame, self.viewer.drawpad.mask)
    if self.dbline.cam_virtual_fps and self.file_end:
      in_ts = 0.0
      self.file_end = False 
    return([3, frame, in_ts])

  async def try_connect(self, maxcounter):
    if self.dbline.cam_pause:
      return()
    self.logger.info(
      f'CA{self.id}: [{maxcounter}] Probing camera #{self.id} ({self.dbline.name})...'
    )
    await self.mycam.ffprobe()
    probe = self.mycam.probe
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
      self.logger.info('+++++ CAM #' + str(self.id) + ': ' + self.dbline.name)
      self.logger.info('+++++ Video codec: ' + self.video_codec_name 
        + ' / Cam: ' + str(self.cam_fps) + 'fps / Connect: ' 
        + str(self.real_fps) + 'fps')
      try:
        streams_redis.x_y_res_to_cam(
          self.id, probe['streams'][self.video_codec]['width'], 
          probe['streams'][self.video_codec]['height'])
      except KeyError:
        self.logger.warning('Key Error in redis.x_y_res_to_cam')
        self.online = False
        return()  
      self.dbline.cam_xres = probe['streams'][self.video_codec]['width']
      self.dbline.cam_yres = probe['streams'][self.video_codec]['height']
      while True:
        try:
          await self.dbline.asave(update_fields=('cam_xres', 'cam_yres',))
          break
        except OperationalError:
          await aclose_old_connections()
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
      while not self.got_sigint:
        await a_break_type(BR_LONG)
        if not self.cam_recording or self.vid_count is None:
          continue
        async with self._mp4_lock:
          if not await aiofiles.os.path.exists(self.vid_file_path(self.vid_count + 2)):
            continue
          try:
            timestamp = await asyncio.to_thread(
              os.path.getmtime, 
              self.vid_file_path(self.vid_count),
            )
          except FileNotFoundError:
            continue
          if timestamp <= self.mp4timestamp:
            continue
          self.mp4timestamp = timestamp
          targetname = self.ts_targetname(timestamp)
          try:
            await aioshutil.move(self.vid_file_path(self.vid_count), 
              self.recordingspath + '/' + targetname)
            await asyncio.to_thread(
              self.myeventer_in.put, 
              ('new_video', self.vid_count, targetname, timestamp)
            )
            self.vid_count += 1
          except FileNotFoundError:
            self.logger.warning(
              f'CA{self.id}: Move did not find: {self.vid_file_path(self.vid_count)}'
            )
    except asyncio.CancelledError:
        return()
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("checkmp4 crashed: %s", fatal, exc_info=True)

  async def watchdog(self):
    try:
      while True:
        try:
          await a_break_time(self.wd_interval)
        except asyncio.CancelledError:
          return()
        if self.dbline.cam_virtual_fps:
          if (streams_redis.check_if_counts_zero('C', self.id)
              and streams_redis.check_if_counts_zero('D', self.id)
              and streams_redis.check_if_counts_zero('E', self.id)):
            continue
          if self.ff_proc is None:
            continue
          if self.ff_proc.returncode is None:
            continue
          else:  
            self.file_end = True
        else:
          timediff = time() - self.wd_ts
          if timediff <= 60:
            continue
          if not self.cam_active:
            self.wd_ts = time()  
            continue
          if (timediff <= 180) and (self.getting_newprozess):
            continue
          if not (streams_redis.view_from_dev('C', self.id)
              or streams_redis.data_from_dev('C', self.id)):
            continue
          self.wd_ts = time()
        if self.got_sigint:
          break
        if self.dbline.cam_virtual_fps:
          self.logger.info(
            f'CA{self.id}: Restarting Video, VirtCam #{self.id} ({self.dbline.name})...', 
          )
        else:
          self.logger.info(
            f'CA{self.id}: Wakeup for Camera #{self.id} ({self.dbline.name})...'
          )
        #if not self.dbline.cam_virtual_fps:
        await self.stopprocess()
        await self.newprocess() 
        self.getting_newprozess = True
    except Exception as fatal:
      self.logger.error('Error in process: ' 
        + self.logname 
        + ' - ' + self.type + str(self.id)
      )
      self.logger.critical("watchdog crashed: %s", fatal, exc_info=True)
    
  def _open_fifo_pair(self):
    self._fifo_dummy_fd = os.open(self.fifo_path, os.O_RDWR | os.O_NONBLOCK)
    rd_fd = os.open(self.fifo_path, os.O_RDONLY | os.O_NONBLOCK)
    return os.fdopen(rd_fd, "rb", buffering=0)
    
  def _raw_reader(self):
    self.raw_running = True
    self.logger.info(f'CA{self.id}: +++++ Starting Reader')
    try:
      while self.raw_running and not self.got_sigint:
        buf = b''
        bytes_left = self.bytes_per_frame
        while bytes_left > 0:
          if not self.raw_running or self.got_sigint:
            buf = b''
            break
          try:
            chunk = os.read(self.fd, bytes_left)
          except BlockingIOError:
            break_type(BR_MEDIUM)
            continue
          except OSError as e:
            self.logger.warning(
              f'CA{self.id}: FD error mid-frame → dropping partial frame: {e}'
            )
            buf = b''
            bytes_left = self.bytes_per_frame
            continue
          if not chunk:
            self.logger.error(
              f'CA{self.id}: EOF mid-frame ({len(buf)} bytes read)'
            )
            return
          buf += chunk
          bytes_left -= len(chunk)
        try:
          self.raw_queue.put(buf, block=False)
        except queue.Full:
          pass
    except Exception as fatal:
      self.logger.critical(
        f'CA{self.id}: Rawfeed crashed: {fatal}',
        exc_info=True
      )
    finally:
      self.logger.info(f'CA{self.id}: ----- Stopping Reader')
      try:
        self.fifo.close()
      except Exception:
        pass
      try:
        os.close(self._fifo_dummy_fd)
      except Exception:
        pass
      self._fifo_dummy_fd = None

  async def newprocess(self):
    self.logger.info('#'+str(self.id) + ' Starting newprocess()')
    while True:
      while True:
        try:
          await self.dbline.arefresh_from_db()
          break
        except OperationalError:
          await aclose_old_connections()
      inp_frame_rate = 0.0
      fps_limit = self.dbline.cam_fpslimit or 0.0
      base_fps = self.dbline.cam_virtual_fps or self.cam_fps
      if fps_limit and fps_limit < base_fps:
        inp_frame_rate = fps_limit
      self.wd_ts = time()
      if self.dbline.cam_virtual_fps:
        base_path = self.virt_cam_path_ram or self.virt_cam_path
        source_string = f"{base_path}{self.dbline.cam_url}"
        filepath = None
      else:
        self.myeventer_in.put(('purge_videos', ))
        source_string = self.dbline.cam_url.replace(
          '{address}', 
          self.dbline.cam_control_ip, 
        )
        if streams_redis.record_from_dev(self.type, self.id):
          self.vid_count = 0
          filepath = (self.recordingspath + 'C' 
            + str(self.id).zfill(4) + '_%08d.mp4')
        else:
          filepath = None
      generalparams = ['-y']
      #**********
      log_ffmpeg = False
      #**********
      if log_ffmpeg:
        generalparams += ['-v', 'info']
      else:  
        generalparams += ['-v', 'fatal']
      if not self.dbline.cam_virtual_fps:
        if source_string[:4].upper() == 'RTSP':
          generalparams += ['-rtsp_transport', 'tcp']
        generalparams += ['-fflags', 'genpts']
        generalparams += ['-use_wallclock_as_timestamps', '1']
        generalparams += ['-flags', 'low_delay']
      inparams = ['-i', source_string]
      outparams1 = []
      if not self.dbline.cam_virtual_fps:
        outparams1 += ['-map', '0:' + str(self.video_codec), '-map', '-0:a']
      outparams1 += ['-vsync', '0']  
      outparams1 += ['-f', 'rawvideo']
      outparams1 += ['-pix_fmt', 'bgr24']
      if inp_frame_rate:
        outparams1 += ['-r', str(inp_frame_rate)]
        outparams1 += ['-fps_mode', 'cfr']
      outparams1 += [self.fifo_path]
      outparams2 = []
      if filepath:
        self.ffmpeg_recording = True
        if self.dbline.cam_ffmpeg_fps and self.dbline.cam_ffmpeg_fps < self.cam_fps:
          video_framerate = self.dbline.cam_ffmpeg_fps
        else:
          video_framerate = None
        outparams2 += ['-map', '0:' + str(self.video_codec)]
        if self.audio_codec > -1:
          outparams2 += ['-map', '0:' + str(self.audio_codec)]
        if self.video_codec_name in {'h264', 'hevc'}:
          if video_framerate:
            outparams2 += ['-c:v', 'libx264']
          else:
            outparams2 += ['-c:v', 'copy']
          if self.audio_codec_name == 'pcm_alaw':
            outparams2 += ['-c:a', 'aac']
          else:
            outparams2 += ['-c:a', 'copy']
        else:    
          outparams2 = ['-c', 'libx264']
        if video_framerate:
          outparams2 += ['-r', str(video_framerate)]
          outparams2 += ['-g', str(round(video_framerate * self.dbline.cam_ffmpeg_segment))]
        outparams2 += ['-f', 'segment']
        outparams2 += ['-segment_time', str(self.dbline.cam_ffmpeg_segment)]
        if video_framerate:
          outparams2 += ['-segment_time_delta', str(0.5 / (video_framerate))]
        outparams2 += ['-reset_timestamps', '1']
        if self.dbline.cam_ffmpeg_crf:
          outparams2 += ['-crf', str(self.dbline.cam_ffmpeg_crf)]
        outparams2 += [filepath]
      else:
        self.ffmpeg_recording = True
      cmd = (generalparams + inparams + outparams1 
        + outparams2)
      self.logger.info('#####' + str(cmd))
      
      self.logger.info('#'+str(self.id) + ' 00000')
      while self.ff_proc is not None and self.ff_proc.returncode is None:
        await a_break_type(BR_LONG)
      self.logger.info('#'+str(self.id) + ' 11111')
      try:
        await aiofiles.os.remove(self.fifo_path)
      except FileNotFoundError:
        pass
      self.logger.info('#'+str(self.id) + ' 22222')
      await asyncio.to_thread(os.mkfifo, self.fifo_path)
      self.logger.info('#'+str(self.id) + ' 33333')
      if log_ffmpeg:
        log = open(logpath + f'ffmpeg{self.id}.log', "ab")
        self.ff_proc = await asyncio.create_subprocess_exec(
          '/usr/bin/ffmpeg',
          *cmd,
          stdout=None,
          stderr=log,
        )
      else:  
        self.ff_proc = await asyncio.create_subprocess_exec(
          '/usr/bin/ffmpeg',
          *cmd,
          stdout=None,
        )
      self.logger.info('#'+str(self.id) + ' 44444')
      try:
        self.fifo = await asyncio.to_thread(self._open_fifo_pair)
        self.fd = self.fifo.fileno()
        self.logger.info('#%s 55555', self.id)
        self.reader_thread = threading.Thread(
          target=self._raw_reader,
          daemon=True,
        )
        self.reader_thread.start()
        break
      except FileNotFoundError:
        self.logger.warning('#%s FIFO fehlt – lege neu an', self.id)
        self.logger.warning(
          f'CA{self.id}: FIFO fehlt – lege neu an'
        )
        await asyncio.to_thread(lambda: (os.makedirs(os.path.dirname(self.fifo_path), exist_ok=True),
                                         os.path.exists(self.fifo_path) or os.mkfifo(self.fifo_path, 0o660)))
        await a_break_time(0.5)
      except OSError as e:
        self.logger.error(
          f'CA{self.id}: Fehler beim Öffnen des Fifos {e}'
        )
        await self.stopprocess()
        return()

  async def stopprocess(self):
    self.logger.info('#'+str(self.id) + ' aaaaa')
    self.raw_running = False
    if self.reader_thread and self.reader_thread.is_alive():
      await asyncio.to_thread(self.reader_thread.join)
    self.logger.info('#'+str(self.id) + ' bbbbb')
    if self.ff_proc is not None and self.ff_proc.returncode is None:
      try:
        p = Process(self.ff_proc.pid)
        for child in p.children(recursive=True):
          try:
            child.kill()
            child.wait()
          except NoSuchProcess:
            pass        
      except NoSuchProcess:
        pass        
      self.logger.info('#'+str(self.id) + ' ccccc')
      try:
        self.ff_proc.send_signal(SIGKILL)
      except ProcessLookupError:
        pass
      self.logger.info('#'+str(self.id) + ' ddddd')
      await self.ff_proc.wait()
      self.logger.info('#'+str(self.id) + ' eeeee')
    self.ff_proc = None
    self.logger.info('#'+str(self.id) + ' fffff')

  def ts_targetname(self, ts):
    return('C'+str(self.id).zfill(4) + '_'
      +ts2filename(ts, noblank = True) + '.mp4')

  def vid_file_path(self, nr):
    return(self.recordingspath + 'C'+str(self.id).zfill(4)
      + '_' + str(nr).zfill(8) + '.mp4')

  async def reset_cam(self):
    if not self.cam_active:
      return()
    await self.stopprocess() 
    self.logger.info('Cam #'+str(self.id)+' is off')
    if self.ff_proc is not None:
      await self.dbline.arefresh_from_db()
      try:
        self.ff_proc.send_signal(SIGINT)
        self.ff_proc.terminate()
        await self.ff_proc.wait()
      except ProcessLookupError:
        self.logger.warning(
          f'CA{self.id}: Process does not exist anymore. Cannot send signal'
        )
      self.ff_proc = None
    self.reset_buffer = True
    await self.newprocess() 
    self.logger.info('Cam #'+str(self.id)+' is on')

  async def set_pause(self, status):
    await asyncio.to_thread(self.inqueue.put, ('pause', status))
    
