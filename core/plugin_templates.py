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
from tools.c_tools import speedlimit, speedometer, rect_atob

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
    
  async def async_init(self):
    self.sl = speedlimit(period = 0.0)
    self.som = speedometer()
    self.div_ts = 0.0
    self.div_old = 1.0
    self.ts_background = time()
    
  async def check_time(self, 
      frame_time, 
      fps_limit, 
      virtual_cam, 
      buffer_size,
      self_id,
      logger, 
    ):  
    if (new_time := time()) - self.div_ts >= 5.0 and not virtual_cam:  
      if buffer_size < 2.5:
        divisor = 1.0  
      elif buffer_size < 5.0:
        divisor = 2.0   
      elif buffer_size < 10.0:
        divisor = 4.0  
      else:  
        divisor = 8.0  
      new_period = 0.0 if fps_limit == 0 else divisor / fps_limit
      if self.sl.period != new_period:
        self.sl.period = new_period
      if divisor != self.div_old:
        self.div_old = divisor
        logger.warning(f'DE{self_id}: Fpm divisor = {divisor}')
      self.div_ts = new_time
    return(self.sl.greenlight(frame_time))
    
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
  ): 
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

