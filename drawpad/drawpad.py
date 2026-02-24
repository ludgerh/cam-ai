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

import numpy as np
import cv2 as cv
from globals.c_globals import viewables
from json import dumps, loads
from shapely.geometry import Point, LinearRing
from channels.db import database_sync_to_async
from .models import mask


MIN_RECT = 75

class ring_class():
  def __init__(self, size = None, xdim = None, ydim = None, input_list = None):
    if input_list is not None:
      self.points = input_list
      xs, ys = zip(*self.points)
      self.min_x, self.max_x = min(xs), max(xs)
      self.min_y, self.max_y = min(ys), max(ys)
      #print('#####', self.min_x, self.max_x, self.min_y, self.max_y)
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
      #print('#####', self.min_x, self.max_x, self.min_y, self.max_y)

class drawpad():
  def __init__(self, parent, logger):
    self.logger = logger
    self.parent = parent
    self.id = parent.id
    self.type = parent.type
    self.edit_active = False
    self.show_mask = False
    self.rectangular = False
    self.whitemarks = True
    self.backgr = (255,255,255)
    self.foregr = (0,0,0)
    self.ringlist = []
    self.mypoint = None
    self.mask = None 
    
  def set_xy(self, size):
    #print('##### set_xy', self.type, self.id, size)
    self.xdim = size[0]
    self.ydim = size[1]  
    self.radius = round(min(self.xdim, self.ydim) / 50)
    
  async def set_mask_local(self, ringlist = None):
    self.ringlist = ringlist
    if self.ringlist is None:
      self.ringlist = []
      items = await database_sync_to_async(list)(
        mask.objects.filter(stream_id=self.id, mtype=self.type), 
      )
      for item in items:
        self.ringlist.append(ring_class(input_list = loads(item.definition)))
    self.make_screen()
    self.mask_from_polygons()   
    
  async def load_ringlist(self):
    self.ringlist = []
    filterlines = mask.objects.filter(stream_id=self.id, mtype=self.type)
    async for item in filterlines:
      self.ringlist.append(ring_class(input_list = loads(item.definition)))

  def draw_rings(self, radius=None, colour=None):
    if radius is None:
      radius = self.radius
    if colour is None:
      colour = self.foregr
    for ring in self.ringlist:
      pts = np.array(ring.points, np.int32)
      cv.polylines(self.screen, [pts], True, colour, 2) 
      for item in ring.points:
        cv.circle(self.screen,(round(item[0]), round(item[1])), radius, colour, -1)

  def make_screen(self, x=None, y=None, radius=None):
    if x is None:
      x = self.xdim
    if y is None:
      y = self.ydim
    if radius is None:
      radius = self.radius
    self.screen = np.full((y, x, 3), self.backgr, np.uint8)
    self.draw_rings(radius)

  def new_ring(self):
    if not self.edit_active:
      return()
    self.ringlist.append(ring_class(
      size = round(min(self.xdim, self.ydim) / 4), 
      xdim = self.xdim, 
      ydim = self.ydim,
    ))

  def mask_from_polygons(self, x=None, y=None, backgr=(255,255,255), foregr=(0,0,0)):
    if x is None:
      x = self.xdim
    if y is None:
      y = self.ydim
    result = np.empty((y, x, 3), np.uint8)
    result[:] = backgr
    for ring in self.ringlist:
      pts = np.array(ring.points).round().astype(np.int32)
      cv.fillPoly(result, [pts], foregr)
    self.mask = result

  def point_clicked(self, x, y):
    click_point = Point(x,y) 
    for i in range(len(self.ringlist)):
      for j in range(len(self.ringlist[i].points)):
        check_point = Point(self.ringlist[i].points[j])
        if check_point.distance(click_point) <= self.radius:
          return((i,j))
    return(None)

  def mousedownhandler(self, x, y):
    self.mypoint = self.point_clicked(x, y) 

  def move_point(self, x, y):
    try:
      buffer = self.ringlist[self.mypoint[0]].points[self.mypoint[1]]
    except IndexError:
      return() 
    self.draw_rings(colour=self.backgr)
    self.ringlist[self.mypoint[0]].points[self.mypoint[1]] = (round(x), round(y))
    testring = LinearRing(self.ringlist[self.mypoint[0]].points)
    if (not testring.is_valid) or (not testring.is_simple):
      self.ringlist[self.mypoint[0]].points[self.mypoint[1]] = buffer
    self.draw_rings()

  def mousemovehandler(self, x, y):
    if self.mypoint is None or not self.ringlist:
      return()
    my_ring = self.ringlist[self.mypoint[0]]
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
        

  async def mouseuphandler(self, x, y):
    if self.mypoint is not None:
      self.mousemovehandler(x, y)
      self.mask_from_polygons()
      masklines = mask.objects.filter(stream_id=self.id, mtype=self.type)
      async for item in masklines:
        await item.adelete()
      for ring in self.ringlist:
        m = mask(
          name = 'New Ring',
          definition = dumps(ring.points),
          stream_id = self.id,
          mtype = self.type
        )
        await m.asave()
      self.mypoint = None
      self.mask_from_polygons()

  async def dblclickhandler(self, x, y):
    self.mypoint = self.point_clicked(x, y) 
    if self.mypoint is not None:
      del self.ringlist[self.mypoint[0]]
      self.mask_from_polygons()
      self.make_screen()
      masklines = mask.objects.filter(stream_id=self.id, mtype=self.type)
      async for item in masklines:
        await item.adelete()
      for ring in self.ringlist:
        m = mask(
          name='New Ring',
          definition=dumps(ring.points),
          stream_id=self.id,
          mtype=self.type
        )
        await m.asave()
      self.draw_rings()
