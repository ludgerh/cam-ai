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

import json
from logging import getLogger
from traceback import format_exc
from django.forms.models import model_to_dict
from django.db import transaction
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from access.c_access import access
from tools.djangodbasync import getoneline, savedbline, deletefilter, updatefilter
from tools.c_logger import log_ini
from tf_workers.models import school
from streams.models import stream
from eventers.models import evt_condition
from streams.startup import streams
from drawpad.models import mask

logname = 'ws_oneitemconsumers'
logger = getLogger(logname)
log_ini(logger, logname)

class oneitemConsumer(AsyncWebsocketConsumer):

  @database_sync_to_async
  def read_conditions(self):
    self.myitem.read_conditions()

  async def connect(self):
    await self.accept()
    self.myitem = None

  async def disconnect(self, close_code):
    if self.myitem is not None:
      self.myitem.nr_of_cond_ed = 0
      self.myitem.last_cond_ed = 0

  async def receive(self, text_data):
    logger.debug('<-- ' + str(text_data))
    params = json.loads(text_data)['data']
    outlist = {'tracker' : json.loads(text_data)['tracker']}

    if params['command'] == 'setmyitem':
      if access.check(params['mode'], params['itemid'], self.scope['user'], 'R'):
        self.mode = params['mode']
        self.idx = params['itemid']
        if self.mode == 'C':
          self.myitem = streams[params['itemid']].mycam
          self.mydrawpad = self.myitem.viewer.drawpad
          self.mydetectordrawpad = self.myitem.mydetector.viewer.drawpad
        elif self.mode == 'D':
          self.myitem = streams[params['itemid']].mydetector
        elif self.mode == 'E':
          self.myitem = streams[params['itemid']].mydetector.myeventer
        self.may_write = access.check(params['mode'], int(params['itemid']), self.scope['user'], 'W')
        self.scaling = params['scaling']
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))	
      else:
        await self.close()

    elif params['command'] == 'setonefield':
      if self.may_write:
        if params['pname'] == 'cam_pause':
          self.myitem.dbline.cam_pause = params['value']
          self.myitem.set_pause(params['value'])
        elif params['pname'] == 'cam_fpslimit':
          self.myitem.dbline.cam_fpslimit = float(params['value'])
        elif params['pname'] == 'cam_feed_type':
          self.myitem.dbline.cam_feed_type = int(params['value'])
        elif params['pname'] == 'cam_url':
          self.myitem.dbline.cam_url = params['value']
        elif params['pname'] == 'cam_repeater':
          self.myitem.dbline.cam_repeater = int(params['value'])
        elif params['pname'] == 'det_fpslimit':
          value = float(params['value'])
          self.myitem.dbline.det_fpslimit = value
          self.myitem.inqueue.put(('set_fpslimit', value))
        elif params['pname'] == 'det_threshold':
          value = int(params['value'])
          self.myitem.dbline.det_threshold = value
          self.myitem.inqueue.put(('set_threshold', value))
        elif params['pname'] == 'det_backgr_delay':
          value = int(params['value'])
          self.myitem.dbline.det_backgr_delay = value
          self.myitem.inqueue.put(('set_backgr_delay', value))
        elif params['pname'] == 'det_dilation':
          value = int(params['value'])
          self.myitem.dbline.det_dilation = value
          self.myitem.inqueue.put(('set_dilation', value))
        elif params['pname'] == 'det_erosion':
          value = int(params['value'])
          self.myitem.dbline.det_erosion = value
          self.myitem.inqueue.put(('set_erosion', value))
        elif params['pname'] == 'det_max_size':
          value = int(params['value'])
          self.myitem.dbline.det_max_size = value
          self.myitem.inqueue.put(('set_max_size', value))
        elif params['pname'] == 'det_max_rect':
          value = int(params['value'])
          self.myitem.dbline.det_max_rect = value
          self.myitem.inqueue.put(('set_max_rect', value))
        elif params['pname'] == 'eve_fpslimit':
          value = float(params['value'])
          self.myitem.dbline.eve_fpslimit = value
          self.myitem.inqueue.put(('set_fpslimit', value))
        elif params['pname'] == 'eve_margin':
          value = int(params['value'])
          self.myitem.dbline.eve_margin = value
          self.myitem.inqueue.put(('set_margin', value))
        elif params['pname'] == 'eve_event_time_gap':
          value = int(params['value'])
          self.myitem.dbline.eve_event_time_gap = value
          self.myitem.inqueue.put(('set_event_time_gap', value))
        elif params['pname'] == 'eve_school':
          value = int(params['value'])
          myschool = await getoneline(school, {'id' : value, })
          self.myitem.dbline.eve_school = myschool 
          self.myitem.inqueue.put(('set_school', value))
        elif params['pname'] == 'eve_alarm_email':
          self.myitem.dbline.eve_alarm_email = params['value']
          self.myitem.inqueue.put(('set_alarm_email', params['value']))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'setcbstatus':
      if self.may_write:
        if 'ch_show' in params:
          self.myitem.viewer.drawpad.show_mask = params['ch_show']
        if 'ch_edit' in params:
          self.myitem.viewer.drawpad.edit_active = params['ch_edit']
        if 'ch_apply' in params:
          self.myitem.inqueue.put(('set_apply_mask', params['ch_apply']))
          myline = await getoneline(stream, {'id' : self.myitem.dbline.id, })
          if self.mode == 'C':
            myline.cam_apply_mask = params['ch_apply']
            await savedbline(myline, ["cam_apply_mask"])
          elif self.mode == 'D':
            myline.det_apply_mask = params['ch_apply']
            await savedbline(myline, ["det_apply_mask"])
        if 'ch_white' in params:
          self.myitem.viewer.drawpad.whitemarks = params['ch_white']
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'setbtevent':
      if self.may_write:
        if 'bt_new' in params:
          self.mydrawpad.new_ring()
          self.mydrawpad.screen = self.mydrawpad.make_screen()
          self.mydrawpad.mask = self.mydrawpad.mask_from_polygons()
        if 'bt_move' in params:
          self.mydetectordrawpad.ringlist = self.mydrawpad.ringlist
          self.mydrawpad.ringlist = []
          self.mydrawpad.screen = self.mydrawpad.make_screen()
          self.mydrawpad.mask = self.mydrawpad.mask_from_polygons()
          self.mydetectordrawpad.screen = self.mydetectordrawpad.make_screen()
          self.mydetectordrawpad.ringlist = self.mydetectordrawpad.reduce_rings_size()
          self.mydetectordrawpad.mask = self.mydetectordrawpad.mask_from_polygons()
          self.myitem.mydetector.inqueue.put(('set_mask', self.mydetectordrawpad.ringlist))
          await deletefilter(mask, {'stream_id' : self.idx, 'mtype' : 'C', })
          await deletefilter(mask, {'stream_id' : self.idx, 'mtype' : 'D', })
          for ring in self.mydetectordrawpad.ringlist:
            m = mask(
              name='New Ring',
              definition=json.dumps(ring),
              stream_id=self.idx,
              mtype='D',
            )
            await savedbline(m)
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'mousedown':
      if self.may_write:
        self.myitem.viewer.drawpad.mousedownhandler(params['x']/self.scaling, params['y'] / self.scaling)
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'mouseup':
      if self.may_write:
       await self.myitem.viewer.drawpad.mouseuphandler(params['x']/self.scaling, params['y'] / self.scaling)
       self.myitem.inqueue.put(('set_mask', self.myitem.viewer.drawpad.ringlist))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'mousemove':
      if self.may_write:
        self.myitem.viewer.drawpad.mousemovehandler(params['x']/self.scaling, params['y'] / self.scaling)
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'dblclick':
      if self.may_write:
       await self.myitem.viewer.drawpad.dblclickhandler(params['x']/self.scaling, params['y'] / self.scaling)
       self.myitem.inqueue.put(('set_mask', self.myitem.viewer.drawpad.ringlist))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'delcondition': #xxx
      if self.may_write:
        await deletefilter(evt_condition, {'id' : params['c_nr']})
        self.myitem.inqueue.put(('del_condition', int(params['reaction']), int(params['c_nr'])))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'getcondition': #xxx
      if self.may_write:
        mydata = await getoneline(evt_condition, {'id' : params['c_nr'], })
      outlist['data'] = model_to_dict(mydata, exclude=[])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'cond_open':
      if self.may_write:
        self.myitem.inqueue.put(('cond_open', int(params['reaction'])))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'cond_close':
      if self.may_write:
        self.myitem.inqueue.put(('cond_close', int(params['reaction'])))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'get_all_conditions':
      await self.read_conditions()
      outlist['data'] = self.myitem.cond_dict
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'cond_to_str': #xxx
      outlist['data'] = self.myitem.build_string(params['condition'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'savecondition': #xxx
      if self.may_write:
        self.myitem.inqueue.put((
          'save_condition', 
          int(params['reaction']), 
          int(params['c_nr']),
          int(params['c_type']),
          int(params['x']),
          float(params['y']),
        ))
        if params['save_db']:
          dbline = await getoneline(evt_condition, {'id' : params['c_nr'], })
          dbline.c_type = int(params['c_type'])
          dbline.x = int(params['x'])
          dbline.y = float(params['y'])
          await savedbline(dbline, ['c_type', 'x', 'y', ])
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'newcondition': #xxx
      if self.may_write:
        dbline = evt_condition(and_or=int(params['and_or']), reaction=int(params['reaction']), 
        eventer_id=self.myitem.dbline.id)
        await savedbline(dbline)
        newitem = model_to_dict(dbline)
        self.myitem.inqueue.put(('new_condition', int(params['reaction']), newitem))
        outlist['data'] = newitem
      else:
        outlist['data'] = 'No Access'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'save_conditions':
      if self.may_write:
        self.myitem.inqueue.put(('save_conditions', params['reaction'], params['conditions']))
        cond_dict = json.loads(params['conditions'])
        await deletefilter(evt_condition, {'eventer_id' : self.myitem.dbline.id, 'reaction' : params['reaction'], }, )
        for item in cond_dict:
          db_line = evt_condition(
            eventer_id = self.myitem.dbline.id,
            reaction = params['reaction'],
            and_or = item['and_or'],
            c_type = item['c_type'],
            x = item['x'],
            y = item['y'],
            bracket = item['bracket'],
          )
          await savedbline(db_line)
        outlist['data'] = 'OK'
        
      else:
        outlist['data'] = 'No Access'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

    elif params['command'] == 'delete_cam':
      if self.may_write:
        if params['itemid'] in streams:
          streams[params['itemid']].stop()
        await updatefilter(stream, {'id' : params['itemid'], }, {'active' : False, })
        outlist['data'] = 'OK'
      else:
        outlist['data'] = 'No Access'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))	

