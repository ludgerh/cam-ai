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

import sys
import numpy as np
import cv2 as cv
from asgiref.sync import sync_to_async
from json import dumps, loads
from shapely.geometry import Point, LinearRing
from django.db import close_old_connections
from channels.db import database_sync_to_async
from globals.c_globals import viewables
from .models import mask as mask_db


MIN_RECT = 75

class ring_class():
  def __init__(self, 
      size = None, 
      xdim = None, 
      ydim = None, 
      input_list = None, 
      idx = None, 
    ):
    self.mask_id = idx
    if input_list is not None:
      self.points = input_list
      xs, ys = zip(*self.points)
      self.min_x, self.max_x = min(xs), max(xs)
      self.min_y, self.max_y = min(ys), max(ys)
    elif size is not None and xdim is not None and ydim is not None:
      cx = round(xdim / 2)
      cy = round(ydim / 2)
      self.min_x = cx - size
      self.max_x = cx + size
      self.min_y = cy - size
      self.max_y = cy + size
      self.points = [
        [self.min_x, self.min_y],
        [self.min_x, cy],
        [self.min_x, self.max_y],
        [cx, self.max_y],
        [self.max_x, self.max_y],
        [self.max_x, cy],
        [self.max_x, self.min_y],
        [cx, self.min_y],
      ]
    
  def len(self):
    return len(self.points)  
    
  async def asave(self, type = None, idx = None):
    if type == 'D':
      target_sh_mem = viewables[idx]['C'].shared_mem
      min_x = target_sh_mem.read_1_meta('aoi_xmin') 
      max_x = target_sh_mem.read_1_meta('aoi_xmax') 
      min_y = target_sh_mem.read_1_meta('aoi_ymin') 
      max_y = target_sh_mem.read_1_meta('aoi_ymax') 
      target_sh_mem = viewables[idx]['D'].shared_mem
      scaledown = target_sh_mem.read_1_meta('scaledown') 
      points_to_save = []
      for item in self.points:
        new_point = [item[0] * scaledown + min_x, item[1] * scaledown + min_y]
        if new_point[0] >= max_x - scaledown + 1:
          new_point[0] = max_x
        if new_point[1] >= max_y - scaledown + 1:
          new_point[1] = max_y
        points_to_save.append(new_point)
    else:
      points_to_save = self.points  
    if self.mask_id is None:
      mask_line = mask_db(
        mtype = type, 
        name = 'New Ring', 
        definition = dumps(points_to_save), 
        stream_id = idx, 
      )
      await mask_line.asave()
      self.mask_id = mask_line.id
    else:
      mask_line = await mask_db.objects.aget(id = self.mask_id)
      mask_line.definition = dumps(points_to_save)
      await mask_line.asave(update_fields=('definition', ))
    
  async def adelete(self):
    mask_line = await mask_db.objects.aget(id = self.mask_id)
    await mask_line.adelete()
      
class ringlist_class():  
  def __init__(self, data = None): 
    if data is None:
      self.rings = []
    else:
      self.rings = data
    if data: 
      self.check_min_max()
    else: #None or []
      self.min_x = sys.maxsize
      self.max_x = -1
      self.min_y = sys.maxsize
      self.max_y = -1  
         
  def check_min_max(self, item = None): 
    if item is None:
      min_xs = [p.min_x for p in self.rings]
      max_xs = [p.max_x for p in self.rings]
      min_ys = [p.min_y for p in self.rings]
      max_ys = [p.max_y for p in self.rings]
      self.min_x = min(min_xs)
      self.max_x = max(max_xs)
      self.min_y = min(min_ys)
      self.max_y = max(max_ys)
    else: 
      self.min_x = min(self.min_x, item.min_x)
      self.max_x = max(self.max_x, item.max_x)
      self.min_y = min(self.min_y, item.min_y)
      self.max_y = max(self.max_y, item.max_y)  
      
  def append(self, item):
    self.rings.append(item) 
    self.check_min_max(item)
    
  def len(self):
    return len(self.rings)
    
  async def adelete(self, type, idx):
    await mask_db.objects.filter(stream_id=idx, mtype=type).adelete()

class drawpad():
  def __init__(self, parent, logger):
    self.logger = logger
    self.parent = parent
    self.id = parent.id
    self.type = parent.type
    if self.type in {'C', 'D'}:
      self.gparent = None
    self.edit_active = False
    self.show_mask = False
    self.rectangular = False
    self.whitemarks = True
    self.backgr = (255,255,255)
    self.foregr = (0,0,0)
    self.ringlist = ringlist_class()
    self.mypoint = None
    self.mask = None 
    self.screen = None
    self.positive_mask = False
    self.xdim = 0
    self.ydim = 0
    self.radius = 0
    
  def set_xy(self, size):
    self.xdim = size[0]
    self.ydim = size[1]  
    self.radius = round(min(self.xdim, self.ydim) / 50)
    
  async def set_mask_local(self, ringlist = None):
    if ringlist is None:
      await self.aload_ringlist()
    else:  
      self.ringlist = ringlist_class(ringlist)
    self.make_screen()
    self.mask_from_polygons() 
    
  def _build_ringlist(self):
      close_old_connections()
      if self.type == 'D':
        target_sh_mem = viewables[self.id]['C'].shared_mem
        min_x = target_sh_mem.read_1_meta('aoi_xmin') 
        min_y = target_sh_mem.read_1_meta('aoi_ymin') 
        target_sh_mem = viewables[self.id]['D'].shared_mem
        scaledown = target_sh_mem.read_1_meta('scaledown') 
        if not scaledown:
          return(None)
      ringlist = ringlist_class()
      for item in mask_db.objects.filter(stream_id=self.id, mtype=self.type):
        if self.type == 'D':
          points_from_db = []
          for point in loads(item.definition):
            points_from_db.append([
              (point[0] - min_x) // scaledown, 
              (point[1] - min_y) // scaledown, 
            ])
        else: 
          points_from_db = loads(item.definition)   
        ringlist.append(ring_class(input_list = points_from_db, idx = item.id))
      return(ringlist)

  def load_ringlist(self):
    self.ringlist = self._build_ringlist()

  async def aload_ringlist(self):
    self.ringlist = await sync_to_async(self._build_ringlist)()

  def draw_rings(self, radius=None, colour=None):
    if radius is None:
      radius = self.radius
    if colour is None:
      colour = self.foregr
    for ring in self.ringlist.rings:
      pts = np.array(ring.points, np.int32)
      cv.polylines(self.screen, [pts], True, colour, 2) 
      for item in ring.points:
        cv.circle(self.screen,(round(item[0]), round(item[1])), radius, colour, -1)

  def make_screen(self, x=None, y=None, radius=None):
    if self.ringlist is None:
      return()
    if x is None:
      x = self.xdim
    if y is None:
      y = self.ydim
    if radius is None:
      radius = self.radius
    self.screen = np.full((y, x, 3), self.backgr, np.uint8)
    self.draw_rings(radius)

  async def new_ring(self):
    if not self.edit_active:
      return()
    my_ring = ring_class(
      size = round(min(self.xdim, self.ydim) / 4), 
      xdim = self.xdim, 
      ydim = self.ydim,
    ) 
    self.ringlist.append(my_ring)
    await my_ring.asave(type = self.type, idx = self.id)

  def mask_from_polygons(self, 
      x = None, 
      y = None, 
      backgr = (255,255,255), 
      foregr = (0,0,0), 
      sh_mem = None, 
    ):
    if x is None:
      x = self.xdim
    if y is None:
      y = self.ydim
    result = np.empty((y, x, 3), np.uint8)
    if self.positive_mask:
      result[:] = foregr
    else:  
      result[:] = backgr
    if self.ringlist is not None:
      for ring in self.ringlist.rings:
        pts = np.array(ring.points).round().astype(np.int32)
        if self.positive_mask:
          cv.fillPoly(result, [pts], backgr)
        else:
          cv.fillPoly(result, [pts], foregr)
    self.mask = result
    if sh_mem is None: 
      if self.gparent is None:
        self.gparent = viewables[self.id][self.type]
      target_sh_mem = self.gparent.shared_mem
    else:  
      target_sh_mem = sh_mem
    if self.type == 'C':   
      if (target_sh_mem.read_1_meta('apply_mask') 
          and self.positive_mask 
          and self.ringlist.len()):
        min_x = self.ringlist.min_x
        max_x = self.ringlist.max_x
        min_y = self.ringlist.min_y
        max_y = self.ringlist.max_y
      else:
        min_x = 0
        max_x = self.xdim - 1
        min_y = 0
        max_y = self.ydim - 1
      target_sh_mem.write_1_meta('aoi_xmin', min_x) 
      target_sh_mem.write_1_meta('aoi_xmax', max_x) 
      target_sh_mem.write_1_meta('aoi_ymin', min_y) 
      target_sh_mem.write_1_meta('aoi_ymax', max_y) 
      target_sh_mem.write_mask(self.mask)
    if self.type == 'D':   
      target_sh_mem.write_mask(self.mask)

  def point_clicked(self, x, y):
    click_point = Point(x,y) 
    print('Click', click_point)
    for i in range(len(self.ringlist.rings)):
      for j in range(len(self.ringlist.rings[i].points)):
        check_point = Point(self.ringlist.rings[i].points[j])
        print('Check', check_point, self.radius)
        if check_point.distance(click_point) <= self.radius:
          return((i,j))
    return(None)

  def mousedownhandler(self, x, y):
    self.mypoint = self.point_clicked(x, y) 

  def move_point(self, x, y):
    print('move_point', x, y)
    try:
      buffer = self.ringlist.rings[self.mypoint[0]].points[self.mypoint[1]]
    except IndexError:
      return() 
    self.draw_rings(colour=self.backgr)
    self.ringlist.rings[self.mypoint[0]].points[self.mypoint[1]] = (round(x), round(y))
    testring = LinearRing(self.ringlist.rings[self.mypoint[0]].points)
    if (not testring.is_valid) or (not testring.is_simple):
      self.ringlist.rings[self.mypoint[0]].points[self.mypoint[1]] = buffer
    self.draw_rings()

  def mousemovehandler(self, x, y):
    if self.mypoint is None or not self.ringlist.rings:
      return()
    my_ring = self.ringlist.rings[self.mypoint[0]]
    new_x = round(min(max(x, 0), self.xdim - 1))
    new_y = round(min(max(y, 0), self.ydim - 1))
    if self.rectangular:
      self.draw_rings(colour=self.backgr)
      if (self.mypoint[1] == 0 
          and new_x < my_ring.max_x - MIN_RECT 
          and new_y < my_ring.max_y - MIN_RECT):
        my_ring.min_x = new_x
        my_ring.min_y = new_y
      elif self.mypoint[1] == 1 and new_x < my_ring.max_x - MIN_RECT:
        my_ring.min_x = new_x
      elif (self.mypoint[1] == 2 
          and new_x < my_ring.max_x - MIN_RECT 
          and new_y > my_ring.min_y + MIN_RECT):
        my_ring.min_x = new_x
        my_ring.max_y = new_y
      elif self.mypoint[1] == 3 and new_y > my_ring.min_y + MIN_RECT:
        my_ring.max_y = new_y
      elif (self.mypoint[1] == 4 
          and new_x > my_ring.min_x + MIN_RECT 
          and new_y > my_ring.min_y + MIN_RECT):
        my_ring.max_x = new_x
        my_ring.max_y = new_y
      elif self.mypoint[1] == 5 and new_x > my_ring.min_x + MIN_RECT:
        my_ring.max_x = new_x
      elif (self.mypoint[1] == 6 
          and new_x > my_ring.min_x + MIN_RECT 
          and new_y < my_ring.max_y - MIN_RECT):
        my_ring.max_x = new_x
        my_ring.min_y = new_y
      elif self.mypoint[1] == 7 and new_y < my_ring.max_y - MIN_RECT:
        my_ring.min_y = new_y
      my_ring.points[0] = (my_ring.min_x, my_ring.min_y)
      my_ring.points[1] = (my_ring.min_x, round((my_ring.min_y + my_ring.max_y) / 2)) 
      my_ring.points[2] = (my_ring.min_x, my_ring.max_y)
      my_ring.points[3] = (round((my_ring.min_x + my_ring.max_x) / 2), my_ring.max_y) 
      my_ring.points[4] = (my_ring.max_x, my_ring.max_y)
      my_ring.points[5] = (my_ring.max_x, round((my_ring.min_y + my_ring.max_y) / 2)) 
      my_ring.points[6] = (my_ring.max_x, my_ring.min_y) 
      my_ring.points[7] = (round((my_ring.min_x + my_ring.max_x) / 2), my_ring.min_y) 
      self.draw_rings()
    else:  
      self.move_point(new_x, new_y)
      xs, ys = zip(*my_ring.points)
      my_ring.min_x, my_ring.max_x = min(xs), max(xs)
      my_ring.min_y, my_ring.max_y = min(ys), max(ys)
    self.ringlist.check_min_max()
        

  async def mouseuphandler(self, x, y):
    if self.mypoint is not None:
      self.mousemovehandler(x, y)
      print('MyPoint', self.ringlist.rings[self.mypoint[0]].mask_id)
      await self.ringlist.rings[self.mypoint[0]].asave(type = self.type, idx = self.id)
      self.mypoint = None
      self.mask_from_polygons()

  async def dblclickhandler(self, x, y):
    self.mypoint = self.point_clicked(x, y) 
    if self.mypoint is not None:
      await self.ringlist.rings[self.mypoint[0]].adelete()
      del self.ringlist.rings[self.mypoint[0]]
      self.mypoint = None
      self.mask_from_polygons()
      self.make_screen()
      self.draw_rings()
