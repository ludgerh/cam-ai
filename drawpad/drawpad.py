# Copyright (C) 2022 Ludger Hellerhoff, ludger@cam-ai.de
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  
# See the GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import numpy as np
import cv2 as cv
from json import dumps, loads
from time import time
from shapely.geometry import Point, LinearRing
from tools.djangodbasync import savedbline, deletefilter
from .models import mask

class drawpad():

  def __init__(self, parent, logger):
    self.logger = logger
    self.parent = parent
    self.myid = self.parent.parent.dbline.id
    self.edit_active = False
    self.show_mask = False
    self.edit_mask = False
    if self.parent.parent.type == 'C':
      self.whitemarks = False
      self.scaledown = 1
    elif self.parent.parent.type == 'D':
      self.whitemarks = True
      self.scaledown = self.parent.parent.scaledown
    self.backgr = (255,255,255)
    self.foregr = (0,0,0)
    self.radius = 20
    self.xdim = self.parent.parent.dbline.cam_xres
    self.ydim = self.parent.parent.dbline.cam_yres
    self.ringlist = []
    for item in mask.objects.filter(stream_id=self.myid, mtype=self.parent.parent.type):
      self.ringlist.append(loads(item.definition))
    self.parent.parent.inqueue.put(('set_mask', self.ringlist))
    self.screen = self.make_screen()
    self.mask = self.mask_from_polygons()
    self.mypoint = None

  def draw_rings(self, drawpad, radius=None, colour=None):
    if radius is None:
      radius = self.radius
    if colour is None:
      colour = self.foregr
    for ring in self.ringlist:
      pts = np.array(ring, np.int32)
      cv.polylines(drawpad, [pts], True, colour, 2) 
      for item in ring:
        cv.circle(drawpad,(round(item[0]), round(item[1])), radius, colour, -1)

  def make_screen(self, x=None, y=None, radius=None):
    if x is None:
      x = self.xdim
    if y is None:
      y = self.ydim
    if radius is None:
      radius = self.radius
    if self.scaledown == 1:
      result = np.full((y, x, 3), self.backgr, np.uint8)
    else:
      result = np.full((y // self.scaledown, x // self.scaledown, 3), self.backgr, np.uint8)
    self.draw_rings(result, radius)
    return(result)

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
    return(result)
    
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
    return(result)  

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
    buffer = self.ringlist[self.mypoint[0]][self.mypoint[1]]
    self.draw_rings(self.screen, colour=self.backgr)
    self.ringlist[self.mypoint[0]][self.mypoint[1]] = (round(x), round(y))
    testring = LinearRing(self.ringlist[self.mypoint[0]])
    if (not testring.is_valid) or (not testring.is_simple):
      self.ringlist[self.mypoint[0]][self.mypoint[1]] = buffer
    self.draw_rings(self.screen)

  def mousemovehandler(self, x, y):
    if self.mypoint is not None:
      self.move_point(min(max(x, 0), self.xdim - 1),
        min(max(y, 0), self.ydim - 1))

  async def mouseuphandler(self, x, y):
    if self.mypoint is not None:
      self.mousemovehandler(x, y)
      self.mask = self.mask_from_polygons()
      await deletefilter(mask, {
        'stream_id' : self.myid,
        'mtype' : self.parent.parent.type,
      })
      for ring in self.ringlist:
        m = mask(
          name='New Ring',
          definition=dumps(ring),
          stream_id=self.myid,
          mtype=self.parent.parent.type
        )
        await savedbline(m)
      self.mypoint = None

  async def dblclickhandler(self, x, y):
    self.mypoint = self.point_clicked(x, y) 
    if self.mypoint is not None:
      del self.ringlist[self.mypoint[0]]
      self.mask = self.mask_from_polygons()
      await deletefilter(mask, {
        'stream_id' : self.myid,
        'mtype' : self.parent.parent.type,
      })
      for ring in self.ringlist:
        m = mask(
          name='New Ring',
          definition=dumps(ring),
          stream_id=self.myid,
          mtype=self.parent.parent.type
        )
        await savedbline(m)
