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

import numpy as np
import cv2 as cv
from camai.version import version
from time import time
from pathlib import Path
from tools.l_tools import load_plugin
from tools.c_tools import speedlimit, speedometer, rect_atob
from schools.c_schools import get_taglist

class temp_plugin():
  name = 'CAM-AI Generic Plugin'
  version = '0.0.0'
  maker = 'The CAM-AI-Team'
  description = '...description...'
  copyright = 'GNU General Public License'
    
class det_plugin(temp_plugin):
  type = 'D'
  name = 'CAM-AI Generic Detector Plugin'
  version = version

  _SH_MEM_ITEMS = {
      'fps_limit' : 'd',
      'edit_active' : 'i',
      'threshold' : 'i',
      'backgr_delay' : 'i',
      'dilation' : 'i',
      'erosion' : 'i',
      'max_size' : 'i',
      'max_rect' : 'i',
      'apply_mask' : 'i',
      'aoi_xdim' : 'i',
      'aoi_ydim' : 'i',
      'scaledown' : 'i',
      'mode_code' : '50p'
  }
  
  def init_shared_mem(self, shared_mem, dbline):
    shared_mem.write_1_meta('fps_limit', dbline.det_fpslimit)
    shared_mem.write_1_meta('threshold', dbline.det_threshold)
    shared_mem.write_1_meta('backgr_delay', dbline.det_backgr_delay)
    shared_mem.write_1_meta('dilation', dbline.det_dilation)
    shared_mem.write_1_meta('erosion', dbline.det_erosion)
    shared_mem.write_1_meta('max_size', dbline.det_max_size)
    shared_mem.write_1_meta('max_rect', dbline.det_max_rect)
    shared_mem.write_1_meta('apply_mask', dbline.det_apply_mask)
    shared_mem.write_1_meta('scaledown', 0)
    shared_mem.write_1_meta('mode_code', dbline.det_mode_code.encode('utf-8'))
    
  async def async_init(self, my_detector):
    self.my_detector = my_detector
    self.speed_factor = 1.0
    self.divisor = 1.0
    self.sl = speedlimit(
      period = self.divisor / self.my_detector.dbline.det_fpslimit / self.speed_factor
    )
    self.som = speedometer()
    self.div_ts = 0.0
    self.div_old = 1.0
    self.ts_background = time()
  
  def set_speed_factor(self, value):
    if value != self.speed_factor:
      #print('$$$$$ New Speed Factor:', value)
      self.speed_factor = value
      if (fps_limit := self.my_detector.shared_mem.read_1_meta('fps_limit')):
        self.sl.period = self.divisor / fps_limit / value
      else:   
        self.sl.period = 0.0
    
  async def check_time(self, my_detector, buffer_size, frame_time, logger):
    if (new_time := time()) - self.div_ts >= 5.0:  
      if buffer_size < 2.5:
        self.divisor = 1.0  
      elif buffer_size < 5.0:
        self.divisor = 2.0   
      elif buffer_size < 10.0:
        self.divisor = 4.0  
      else:  
        self.divisor = 8.0  
      if (fps_limit := my_detector.shared_mem.read_1_meta('fps_limit')):
        new_period = self.divisor / fps_limit
      else:   
        new_period = 0.0
      if self.sl.period != new_period:
        self.sl.period = new_period / self.speed_factor
      if self.divisor != self.div_old:
        self.div_old = self.divisor
        logger.warning(f'DE{my_detector.id}: Fpm divisor = {self.divisor}')
      self.div_ts = new_time  
    return(self.sl.greenlight(frame_time))
    
  async def async_stop(self, my_detector):
    pass
    
  async def process_frame(self, 
    frame, 
    last_frame, 
    background, 
    mask, 
    edit_active, 
    threshold, 
    erosion, 
    dilation, 
    backgr_delay, 
    mode_code,
  ): 
    self.mode_code = mode_code
    if (mask is not None 
        and not edit_active 
        and frame.shape[:2] == mask.shape[:2]): 
      frame = cv.bitwise_and(frame, mask)
    frame_unmodified = frame.copy() 
    total_diff = np.max(cv.absdiff(last_frame, frame), axis=2)
    if edit_active:
      return((frame, last_frame, background, []))
    _, thresh = cv.threshold(total_diff, threshold, 255, cv.THRESH_BINARY)
    if erosion:
        kernel = np.ones((erosion*2+1, erosion*2+1), np.uint8)
        eroded = cv.erode(thresh, kernel, iterations=1)
    else:
        eroded = thresh
    if dilation:
        kernel = np.ones((dilation*2+1, dilation*2+1), np.uint8)
        dilated = cv.dilate(eroded, kernel, iterations=1)
    else:
        dilated = eroded
    background_mask = cv.bitwise_not(dilated)
    zeros = np.zeros_like(thresh)
    frame_bgr = cv.merge([thresh, zeros, thresh]) 
    eroded_bgr = cv.cvtColor(eroded, cv.COLOR_GRAY2BGR)
    dilated_bgr = cv.cvtColor(dilated, cv.COLOR_GRAY2BGR)
    frame = cv.addWeighted(dilated_bgr, 0.2, frame_bgr, 1, 0)
    frame = cv.add(frame, eroded_bgr)
    _, _, stats, _ = cv.connectedComponentsWithStats(dilated, connectivity=8)
    rect_list = [rect_atob(item) for item in stats[1:]]
    if backgr_delay == 0:
      last_frame = frame_unmodified
    else:
      if (time() >= (self.ts_background + backgr_delay)): 
        self.ts_background = time()
        cv.accumulateWeighted(frame_unmodified, background, 0.1)
      else:
        cv.accumulateWeighted(frame_unmodified, background, 0.5, background_mask)
      last_frame = np.uint8(background) 
    return((frame, last_frame, background, rect_list))
    
class alarm_plugin(temp_plugin):
  type = 'A'
  name = 'CAM-AI Generic Console Alarm Plugin'
  version = version
  
  def __init__(self, eve_dbline, tag_list, plugin_path, logger):
    self.logger = logger
    self.eve_dbline = eve_dbline
    self.tag_list = tag_list
    plugin_mod = load_plugin(plugin_path)
    plugin_dir = Path(plugin_path).parent
    settings_path = plugin_dir / "settings.py"
    self.settings = load_plugin(settings_path)
    
  def action(self, predictions):
    mylist = list(predictions)[1:]
    maxpos = mylist.index(max(mylist))
    self.logger.info(f'{self.settings.settings['output']} {self.eve_dbline.name}'
      f'({self.eve_dbline.id}) : {self.tag_list[maxpos+1].name}')
      

