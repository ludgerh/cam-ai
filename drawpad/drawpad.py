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

import numpy as np
import cv2 as cv
from globals.c_globals import viewables
from json import dumps, loads
from shapely.geometry import Point, LinearRing
from channels.db import database_sync_to_async
from .models import mask

class drawpad():
  def __init__(self, parent, logger):
    self.logger = logger
    self.parent = parent
    self.edit_active = False
    self.show_mask = False
    self.edit_mask = False
    if self.parent.type == 'C':
      self.whitemarks = False
    elif self.parent.type == 'D':
      self.whitemarks = True
    self.scaledown = self.parent.scaledown
    self.backgr = (255,255,255)
    self.foregr = (0,0,0)
    self.radius = 20
    self.xdim = self.parent.xdim
    self.ydim = self.parent.ydim
    self.ringlist = []
    self.mask_set = False
    self.mypoint = None
    self.mask = None 
    
  async def set_mask_local(self, ringlist=None):
    self.ringlist = ringlist
    if not self.ringlist:
      self.ringlist = []
      items = await database_sync_to_async(list)(
        mask.objects.filter(stream_id=self.myid, mtype=self.mtype), 
      )
      for item in items:
        self.ringlist.append(loads(item.definition))
    self.make_screen()
    self.mask_from_polygons()    
    self.mask_set = True        
    
  async def load_ringlist(self):
    self.ringlist = []
    filterlines = mask.objects.filter(stream_id=self.myid, mtype=self.mtype)
    async for item in filterlines:
      self.ringlist.append(loads(item.definition))

  def draw_rings(self, radius=None, colour=None):
    if radius is None:
      radius = self.radius
    if colour is None:
      colour = self.foregr
    for ring in self.ringlist:
      pts = np.array(ring, np.int32)
      cv.polylines(self.screen, [pts], True, colour, 2) 
      for item in ring:
        cv.circle(self.screen,(round(item[0]), round(item[1])), radius, colour, -1)

  def make_screen(self, x=None, y=None, radius=None):
    if x is None:
      x = self.xdim
    if y is None:
      y = self.ydim
    if radius is None:
      radius = self.radius
    if self.scaledown == 1:
      self.screen = np.full((y, x, 3), self.backgr, np.uint8)
    else:
      self.screen = np.full((y // self.scaledown, x // self.scaledown, 3), self.backgr, np.uint8)
    self.draw_rings(radius)

  def new_ring(self):
    size = 100
    myring = [
      [round(self.xdim/2-size), round(self.ydim/2-size)], 
      [round(self.xdim/2-size), round(self.ydim/2)], 
      [round(self.xdim/2-size), round(self.ydim/2+size)], 
      [round(self.xdim/2), round(self.ydim/2+size)], 
      [round(self.xdim/2+size), round(self.ydim/2+size)], 
      [round(self.xdim/2+size), round(self.ydim/2)], 
      [round(self.xdim/2+size), round(self.ydim/2-size)], 
      [round(self.xdim/2), round(self.ydim/2-size)],
    ]
    self.ringlist.append(myring)

  def mask_from_polygons(self, x=None, y=None, backgr=(255,255,255), foregr=(0,0,0)):
    if x is None:
      x = self.xdim
    if y is None:
      y = self.ydim
    result = np.empty((y // self.scaledown, x // self.scaledown, 3), np.uint8)
    result[:] = backgr
    for ring in self.ringlist:
      pts = np.array(ring).round().astype(np.int32)
      cv.fillPoly(result, [pts], foregr)
    self.mask = result
    
  def reduce_rings_size(self):  
    if self.scaledown == 1:
      result = self.ringlist
    else:
      result = []  
      for ring in self.ringlist:
        newring = []
        for point in ring:
          newpoint = [point[0] // self.scaledown, point[1] // self.scaledown] 
          newring.append(newpoint)
        result.append(newring)   
    self.ringlist = result 

  def point_clicked(self, x, y):
    click_point = Point(x,y) 
    for i in range(len(self.ringlist)):
      for j in range(len(self.ringlist[i])):
        check_point = Point(self.ringlist[i][j])
        if check_point.distance(click_point) <= self.radius:
          return((i,j))
    return(None)

  def mousedownhandler(self, x, y):
    self.mypoint = self.point_clicked(x, y) 

  def move_point(self, x, y):
    try:
      buffer = self.ringlist[self.mypoint[0]][self.mypoint[1]]
    except IndexError:
      return() 
    self.draw_rings(colour=self.backgr)
    self.ringlist[self.mypoint[0]][self.mypoint[1]] = (round(x), round(y))
    testring = LinearRing(self.ringlist[self.mypoint[0]])
    if (not testring.is_valid) or (not testring.is_simple):
      self.ringlist[self.mypoint[0]][self.mypoint[1]] = buffer
    self.draw_rings()

  def mousemovehandler(self, x, y):
    if self.mypoint is not None:
      self.move_point(min(max(x, 0), self.xdim - 1),
        min(max(y, 0), self.ydim - 1))

  async def mouseuphandler(self, x, y):
    if self.mypoint is not None:
      self.mousemovehandler(x, y)
      self.mask_from_polygons()
      masklines = mask.objects.filter(stream_id=self.myid, mtype=self.mtype)
      async for item in masklines:
        await item.adelete()
      for ring in self.ringlist:
        m = mask(
          name='New Ring',
          definition=dumps(ring),
          stream_id=self.myid,
          mtype=self.mtype
        )
        await m.asave()
      self.mypoint = None

  async def dblclickhandler(self, x, y):
    self.mypoint = self.point_clicked(x, y) 
    if self.mypoint is not None:
      del self.ringlist[self.mypoint[0]]
      self.mask_from_polygons()
      self.make_screen()
      masklines = mask.objects.filter(stream_id=self.myid, mtype=self.mtype)
      async for item in masklines:
        await item.adelete()
      for ring in self.ringlist:
        m = mask(
          name='New Ring',
          definition=dumps(ring),
          stream_id=self.myid,
          mtype=self.mtype
        )
        await m.asave()
      self.draw_rings()
