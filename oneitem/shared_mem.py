"""
Copyright (C) 2024-2026 by the CAM-AI team, info@cam-ai.de
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

import struct
import numpy as np
from multiprocessing import shared_memory

class shared_mem():
  def __init__(self, source_dict, shape = None, shm_name = None):
    self.source_dict = source_dict
    self.shape = shape
    if self.shape is None:
      new_items = {}
    else:  
      new_items = {
        'my_xdim' : 'i', 
        'my_ydim' : 'i',
        'my_same_size' : 'i',
      }
    self.source_dict = {**new_items, **source_dict}
    self.offsets = {}
    self.meta_format = []
    count = 0
    for item in self.source_dict:
      self.offsets[item] = count
      count += struct.calcsize(self.source_dict[item])
      self.meta_format.append(self.source_dict[item])
    self.dtype = np.uint8
    # metadata layout
    self.meta_format = ' '.join(self.meta_format)
    self.meta_size = struct.calcsize(self.meta_format)
    #print('*****', self.offsets)
    #print('*****', self.meta_format)
    if shm_name is None:
      # c_cam process
      if self.shape is None:
        frame_bytes = 0
      else:  
        frame_bytes = np.prod(shape) * np.dtype(self.dtype).itemsize
      total_size = self.meta_size + frame_bytes
      # create shared memory
      self.shm = shared_memory.SharedMemory(create=True, size=total_size)
    else:  
      # cam_worker process
      self.shm = shared_memory.SharedMemory(name=shm_name)
    # numpy view into frame part
    if self.shape is not None:
      self.frame = np.ndarray(
        shape,
        dtype=self.dtype,
        buffer=self.shm.buf[self.meta_size:]
      )
    
  def write_mask(self, mask):
    #print('##### WriteMask:', mask.shape)
    self.write_1_meta('my_xdim', mask.shape[1])
    self.write_1_meta('my_ydim', mask.shape[0])
    self.write_1_meta(
      'my_same_size', 
      (same_size := (mask.shape[:2] == self.frame.shape[:2]))
    )
    if same_size:
      self.frame[:] = mask
    else: 
      x = self.read_1_meta('my_xdim')
      y = self.read_1_meta('my_ydim')
      self.frame[:y, :x, :] = mask
      
  def read_mask(self):  
    if self.read_1_meta('my_same_size'):
      return(self.frame)
    else:  
      x = self.read_1_meta('my_xdim')
      y = self.read_1_meta('my_ydim')
      return(self.frame[:y, :x, :])
    #print('##### ReadMask:', self.frame.shape)

  def write_1_meta(self, field, value):
    #if field == 'scaledown':
    #  print('###### write_1_meta:', field, value)
    struct.pack_into(self.source_dict[field], self.shm.buf, self.offsets[field], value)
    
  def read_1_meta(self, field):
    result = struct.unpack_from(self.source_dict[field], self.shm.buf, self.offsets[field])[0]
    #if field == 'scaledown':
    #  print('###### read_1_meta:', field, ', got', result)
    return(result)
