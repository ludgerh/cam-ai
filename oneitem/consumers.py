"""
Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
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

import json
from logging import getLogger
from traceback import format_exc
from django.forms.models import model_to_dict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from autobahn.exception import Disconnected
from access.c_access import access
#from tools.djangodbasync import deletefilter
from tools.c_logger import log_ini
from tools.c_redis import myredis
from tf_workers.models import school
from streams.models import stream
from eventers.models import evt_condition
from streams.startup import streams
from drawpad.models import mask

logname = 'ws_oneitem'
logger = getLogger(logname)
log_ini(logger, logname)

redis = myredis()

class oneitemConsumer(AsyncWebsocketConsumer):

  @database_sync_to_async
  def read_conditions(self):
    self.myitem.read_conditions()

  async def connect(self):
    try:
      await self.accept()
      self.myitem = None
      self.detectormask_changed = False
    except:
      logger.error('Error in consumer: ' + logname + ' (oneitem)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def disconnect(self, close_code):
    try:
      if self.myitem is not None:
        self.myitem.nr_of_cond_ed = 0
        self.myitem.last_cond_ed = 0
      if self.detectormask_changed:
        self.mydetectordrawpad.ringlist = self.mydrawpad.ringlist
        self.mydetectordrawpad.make_screen()
        self.mydetectordrawpad.reduce_rings_size()
        self.mydetectordrawpad.mask_from_polygons()
        self.myitem.mydetector.inqueue.put((
          'set_mask', 
          self.mydetectordrawpad.ringlist
        ))
        masklines = mask.objects.filter(stream_id=self.idx, mtype='D',)
        async for item in masklines:
          await item.adelete()
        for ring in self.mydetectordrawpad.ringlist:
          m = mask(
            name='New Ring',
            definition=json.dumps(ring),
            stream_id=self.idx,
            mtype='D',
          )
          await m.asave()
    except:
      logger.error('Error in consumer: ' + logname + ' (oneitem)')
      logger.error(format_exc())
      logger.handlers.clear()

  async def safe_send(self, answer):
    try:
      await self.send(json.dumps(answer))	
    except Disconnected: 
      logger.warning('oneitem.consumers: Safe_send had disconnected websocket') 

  async def receive(self, text_data):
    try:
      logger.debug('<-- ' + str(text_data))
      params = json.loads(text_data)['data']
      outlist = {'tracker' : json.loads(text_data)['tracker']}

      if params['command'] == 'setmyitem':
        if await access.check_async(params['mode'], params['itemid'], self.scope['user'], 'R'):
          self.mode = params['mode']
          self.idx = params['itemid']
          self.mycamitem = streams[params['itemid']].mycam
          if self.mode == 'C':
            self.myitem = streams[params['itemid']].mycam
            self.mydrawpad = self.myitem.viewer.drawpad
            self.mydetectordrawpad = self.myitem.mydetector.viewer.drawpad
          elif self.mode == 'D':
            self.myitem = streams[params['itemid']].mydetector
            self.mydrawpad = self.myitem.viewer.drawpad
          elif self.mode == 'E':
            self.myitem = streams[params['itemid']].mydetector.myeventer
          self.may_write = await access.check_async(
            params['mode'], 
            int(params['itemid']), 
            self.scope['user'], 'W'
          )
          self.scaling = params['scaling']
          outlist['data'] = {}
          if (redis_data := redis.get_ptz(self.idx)):
            outlist['data']['ptz'] = redis_data
          logger.debug('--> ' + str(outlist))
          await self.safe_send(outlist)
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
            myschool = await school.objects.aget(id = value)
            self.myitem.dbline.eve_school = myschool 
            self.myitem.inqueue.put(('set_school', value))
          elif params['pname'] == 'eve_alarm_email':
            self.myitem.dbline.eve_alarm_email = params['value']
            self.myitem.inqueue.put(('set_alarm_email', params['value']))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'setcbstatus':
        if self.may_write:
          if 'ch_show' in params:
            if self.mydrawpad.mtype == 'C':
              self.myitem.viewer.drawpad.show_mask = params['ch_show']
          if 'ch_edit' in params:
            self.myitem.viewer.drawpad.edit_active = params['ch_edit']
          if 'ch_apply' in params:
            myline = await stream.objects.aget(id = self.myitem.dbline.id)
            if self.mode == 'C':
              if self.mydrawpad.mtype == 'C':
                self.myitem.inqueue.put(('set_apply_mask', params['ch_apply']))
              if self.mydrawpad.mtype == 'C':
                myline.cam_apply_mask = params['ch_apply']
                await myline.asave(update_fields=(("cam_apply_mask"), ))
              elif self.mydrawpad.mtype == 'D':
                myline.det_apply_mask = params['ch_apply']
                await myline.asave(update_fields=(("det_apply_mask"), ))
            elif self.mode == 'D':
              self.myitem.inqueue.put(('set_apply_mask', params['ch_apply']))
              myline.det_apply_mask = params['ch_apply']
              await myline.asave(update_fields=(("det_apply_mask"), ))
          if 'ch_white' in params:
            self.myitem.viewer.drawpad.whitemarks = params['ch_white']
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'm_select_change':
        if self.may_write:
          self.mydrawpad.mtype = params['new_val']
          await self.mydrawpad.load_ringlist()
          self.mydrawpad.make_screen()
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'setbtevent':
        if self.may_write:
          if 'bt_new' in params:
            self.mydrawpad.new_ring()
            self.mydrawpad.make_screen()
            self.mydrawpad.mask_from_polygons()
            await mask.objects.filter(
              stream_id=self.idx, 
              mtype=self.mydrawpad.mtype
            ).adelete()
            #await deletefilter(mask, {
            #  'stream_id' : self.idx,
            #  'mtype' : self.mydrawpad.mtype,
            #})
            for ring in self.mydrawpad.ringlist:
              m = mask(
                name='New Ring',
                definition=json.dumps(ring),
                stream_id=self.idx,
                mtype=self.mydrawpad.mtype,
              )
              await m.asave()
            if self.mydrawpad.mtype == 'X':
              self.detectormask_changed = True
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'mousedown':
        if self.myitem.viewer.drawpad.edit_active:
          if self.may_write:
            self.myitem.viewer.drawpad.mousedownhandler(
              params['x']/self.scaling, params['y'] / self.scaling)
        else:
          if self.mycamitem.mycam and self.mycamitem.mycam.myptz:
            self.mycamitem.inqueue.put(('ptz_mdown', params['x']/self.scaling, params['y']/self.scaling))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'mouseup':
        if self.myitem.viewer.drawpad.edit_active:
          if self.may_write:
            await self.myitem.viewer.drawpad.mouseuphandler(
              params['x']/self.scaling, params['y'] / self.scaling)
            self.myitem.inqueue.put(('set_mask', self.myitem.viewer.drawpad.ringlist))
            if self.mydrawpad.mtype == 'X':
              self.detectormask_changed = True
        else:
          if self.mycamitem.mycam and self.mycamitem.mycam.myptz:
            self.mycamitem.inqueue.put(('ptz_mup', params['x']/self.scaling, params['y']/self.scaling))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'mousemove':
        if self.myitem.viewer.drawpad.edit_active:
          if self.may_write:
            self.myitem.viewer.drawpad.mousemovehandler(
              params['x'] / self.scaling, params['y'] / self.scaling)
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'dblclick':
        if self.may_write:
          await self.myitem.viewer.drawpad.dblclickhandler(
            params['x'] / self.scaling, params['y'] / self.scaling)
          self.myitem.inqueue.put(('set_mask', self.myitem.viewer.drawpad.ringlist))
          if self.mydrawpad.mtype == 'X':
            self.detectormask_changed = True
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'mousewheel':
        self.mycamitem.inqueue.put(('ptz_zoom', params['y']))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'zoom_abs':
        self.mycamitem.inqueue.put(('zoom_abs', params['y']))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'pos_rel':
        self.mycamitem.inqueue.put(('pos_rel', params['x'], params['y']))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'getptz':
        outlist['data'] = redis.get_ptz_pos(self.idx)
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'delcondition': #xxx
        if self.may_write:
          filterline = await evt_condition.objects.aget(id=params['c_nr'])
          await filterline.adelete()
          self.myitem.inqueue.put(
            ('del_condition', int(params['reaction']), int(params['c_nr'])))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'getcondition': #xxx
        if self.may_write:
          filterline = await evt_condition.objects.aget(id=params['c_nr'])
        outlist['data'] = model_to_dict(filterline, exclude=[])
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'cond_open':
        if self.may_write:
          self.myitem.inqueue.put(('cond_open', int(params['reaction'])))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'cond_close':
        if self.may_write:
          self.myitem.inqueue.put(('cond_close', int(params['reaction'])))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'get_all_conditions':
        await self.read_conditions()
        outlist['data'] = self.myitem.cond_dict
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'cond_to_str': 
        outlist['data'] = self.myitem.build_string(params['condition'])
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'savecondition': 
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
            dbline = await evt_condition.objects.aget(id=params['c_nr'])
            dbline.c_type = int(params['c_type'])
            dbline.x = int(params['x'])
            dbline.y = float(params['y'])
            await dbline.asave(update_fields=('c_type', 'x', 'y'))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'newcondition': #xxx
        if self.may_write:
          dbline = evt_condition(
            and_or=int(params['and_or']), 
            reaction=int(params['reaction']), 
            eventer_id=self.myitem.dbline.id)
          await dbline.asave()
          newitem = model_to_dict(dbline)
          self.myitem.inqueue.put(('new_condition', int(params['reaction']), newitem))
          outlist['data'] = newitem
        else:
          outlist['data'] = 'No Access'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'save_conditions':
        if self.may_write:
          self.myitem.inqueue.put((
            'save_conditions', params['reaction'], params['conditions']))
          cond_dict = json.loads(params['conditions'])
          conditionlines = evt_condition.objects.filter(eventer_id=self.myitem.dbline.id, reaction=params['reaction'])
          async for item in conditionlines:
            await item.adelete()
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
            await db_line.asave()
          outlist['data'] = 'OK'
        else:
          outlist['data'] = 'No Access'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'delete_cam':
        if self.may_write:
          if params['itemid'] in streams:
            streams[params['itemid']].stop()
          streamline = await stream.objects.aget(id=params['itemid'])
          streamline.active = False
          await streamline.asave(update_fields=(("active"), ))
          outlist['data'] = 'OK'
        else:
          outlist['data'] = 'No Access'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	
    except:
      logger.error('Error in consumer: ' + logname + ' (oneitem)')
      logger.error(format_exc())
      logger.handlers.clear()

