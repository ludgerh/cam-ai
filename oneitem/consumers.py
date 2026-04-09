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

import json
from logging import getLogger
from traceback import format_exc
from django.forms.models import model_to_dict
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import aclose_old_connections
from autobahn.exception import Disconnected
from access.c_access import access
from tools.c_logger import log_ini
from tf_workers.models import school
from streams.models import stream
from streams.redis import my_redis as streams_redis
from globals.c_globals import viewers, viewables
from eventers.models import evt_condition
from drawpad.models import mask

logname = 'ws_oneitem'
logger = getLogger(logname)
log_ini(logger, logname)

class oneitemConsumer(AsyncWebsocketConsumer):

  async def connect(self):
    try:
      await aclose_old_connections()
      await self.accept()
      self.myitem = None
      self.detectormask_changed = False
    except:
      logger.error('Error in consumer: ' + logname + ' (oneitem)')
      logger.error(format_exc())

  async def disconnect(self, code = None):
    try:
      try:
        self.my_viewer.drawpad.edit_active = False
      except AttributeError:
          pass  # ignore missing attributes
      if self.myitem is not None:
        self.myitem.nr_of_cond_ed = 0
        self.myitem.last_cond_ed = 0
    except:
      logger.error('Error in consumer: ' + logname + ' (oneitem)')
      logger.error(format_exc())

  async def safe_send(self, answer):
    try:
      await self.send(json.dumps(answer))	
    except Disconnected: 
      logger.warning('oneitem.consumers: Safe_send had disconnected websocket') 

  async def receive(self, text_data):
    try:
      params = json.loads(text_data)['data']
      #if params['command'] != 'mousemove':
      #  logger.info('<-- ' + str(text_data))
      outlist = {'tracker' : json.loads(text_data)['tracker']}

      if params['command'] == 'setmyitem':
        if await access.check_async(
              params['type'], 
              params['itemid'], 
              self.scope['user'], 
              'R', 
            ):
          self.type = params['type']
          self.idx = params['itemid']
          self.v_client_nr = params['onf_nr']
          self.dbline = await stream.objects.aget(id = self.idx)
          self.mycamitem = viewables[params['itemid']]['C']
          self.myitem = viewables[params['itemid']][self.type]
          self.my_viewer = self.myitem.viewer
          if self.type in {'C', 'D'}:
            self.mydrawpad = self.my_viewer.drawpad
          elif self.type == 'E':
            self.myitem.shared_mem.write_1_meta('x_canvas', params['x_screen'] - 60)
          self.may_write = await access.check_async(
            params['type'], 
            int(params['itemid']), 
            self.scope['user'], 'W'
          )
          outlist['data'] = {}
          if (redis_data := streams_redis.get_ptz(self.idx)):
            outlist['data']['ptz'] = redis_data
          #logger.info('--> ' + str(outlist))
          await self.safe_send(outlist)
        else:
          await self.close()

      elif params['command'] == 'setonefield':
        if self.may_write:
          if params['pname'] == 'cam_pause':
            self.dbline.cam_pause = params['value']
            self.myitem.shared_mem.write_1_meta('apply_pause', bool(params['value']))
          elif params['pname'] == 'cam_fpslimit':
            self.dbline.cam_fpslimit = float(params['value'])
          elif params['pname'] == 'cam_feed_type':
            self.dbline.cam_feed_type = int(params['value'])
          elif params['pname'] == 'cam_url':
            self.dbline.cam_url = params['value']
          elif params['pname'] == 'cam_repeater':
            self.dbline.cam_repeater = int(params['value'])
          elif params['pname'] == 'det_fpslimit':
            value = float(params['value'])
            self.myitem.shared_mem.write_1_meta('fps_limit', value)
            self.dbline.det_fpslimit = value
          elif params['pname'] == 'det_threshold':
            value = int(params['value'])
            self.dbline.det_threshold = value
            self.myitem.shared_mem.write_1_meta('threshold', int(params['value']))
          elif params['pname'] == 'det_backgr_delay':
            value = int(params['value'])
            self.myitem.shared_mem.write_1_meta('backgr_delay', value)
            self.dbline.det_backgr_delay = value
          elif params['pname'] == 'det_dilation':
            value = int(params['value'])
            self.myitem.shared_mem.write_1_meta('dilation', value)
            self.dbline.det_dilation = value
          elif params['pname'] == 'det_erosion':
            value = int(params['value'])
            self.myitem.shared_mem.write_1_meta('erosion', value)
            self.dbline.det_erosion = value
          elif params['pname'] == 'det_max_size':
            value = int(params['value'])
            self.myitem.shared_mem.write_1_meta('max_size', value)
            self.dbline.det_max_size = value
          elif params['pname'] == 'det_max_rect':
            value = int(params['value'])
            self.myitem.shared_mem.write_1_meta('max_rect', value)
            self.dbline.det_max_rect = value
          elif params['pname'] == 'eve_fpslimit':
            value = float(params['value'])
            self.dbline.eve_fpslimit = value
            self.myitem.shared_mem.write_1_meta('fps_limit', value)
          elif params['pname'] == 'eve_margin':
            value = int(params['value'])
            self.dbline.eve_margin = value
            self.myitem.shared_mem.write_1_meta('margin', value)
          elif params['pname'] == 'eve_event_time_gap':
            value = round(float(params['value']))
            self.dbline.eve_event_time_gap = value
            self.myitem.shared_mem.write_1_meta('event_time_gap', value)
          elif params['pname'] == 'eve_shrink_factor':
            value = float(params['value'])
            self.dbline.eve_shrink_factor = value
            self.myitem.shared_mem.write_1_meta('shrink_factor', value)
          elif params['pname'] == 'eve_sync_factor':
            value = float(params['value'])
            self.dbline.eve_sync_factor = value
            self.myitem.shared_mem.write_1_meta('sync_factor', value)
          elif params['pname'] == 'eve_school':
            value = int(params['value'])
            self.dbline.eve_school = await school.objects.aget(id = value)
            self.myitem.shared_mem.write_1_meta('school', value)
          elif params['pname'] == 'eve_alarm_max_nr':
            value = int(params['value'])
            self.dbline.eve_alarm_max_nr = value
            self.myitem.shared_mem.write_1_meta('alarm_max_nr', value)
          elif params['pname'] == 'eve_alarm_email':
            self.dbline.eve_alarm_email = params['value']
            self.myitem.eve_worker.inqueue.put(('set_alarm_email', params['value']))
          elif params['pname'] == 'eve_one_frame_per_event':
            self.dbline.eve_eve_one_frame_per_event = params['value']
            self.myitem.shared_mem.write_1_meta('one_frame_per_event', params['value'])
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'setcbstatus':
        if self.may_write:
          if 'ch_show' in params:
            self.my_viewer.drawpad.show_mask = params['ch_show']
          if 'ch_edit' in params:
            self.my_viewer.drawpad.edit_active = params['ch_edit']
            if self.type == 'D':
              self.myitem.shared_mem.write_1_meta('edit_active', params['ch_edit'])
          if 'ch_apply' in params:
            self.myitem.shared_mem.write_1_meta('apply_mask', params['ch_apply'])
            if self.type == 'C':
              await self.my_viewer.drawpad.set_mask_local()
              self.myitem.shared_mem.write_mask(self.my_viewer.drawpad.mask) 
              self.dbline.cam_apply_mask = params['ch_apply']
              await self.dbline.asave(update_fields=('cam_apply_mask', ))
            elif self.type == 'D':
              self.dbline.det_apply_mask = params['ch_apply']
              await self.dbline.asave(update_fields=('det_apply_mask', ))
          if 'ch_white' in params:
            self.my_viewer.drawpad.whitemarks = params['ch_white']
          if 'ch_positive' in params:
            if self.type == 'C':
              self.my_viewer.drawpad.positive_mask = params['ch_positive']
              await self.my_viewer.drawpad.set_mask_local()
              self.myitem.shared_mem.write_mask(self.my_viewer.drawpad.mask) 
              self.dbline.cam_positive_mask = params['ch_positive']
              await self.dbline.asave(update_fields=('cam_positive_mask', ))
            elif self.type == 'D':
              self.my_viewer.drawpad.positive_mask = params['ch_positive']
              await self.my_viewer.drawpad.set_mask_local()
              self.myitem.shared_mem.write_mask(self.my_viewer.drawpad.mask)
              self.dbline.det_positive_mask = params['ch_positive'] 
              await self.dbline.asave(update_fields=('det_positive_mask', ))
          if 'ch_rectangular' in params:
            self.my_viewer.drawpad.rectangular = params['ch_rectangular']
            if self.my_viewer.drawpad.rectangular:
              await self.my_viewer.drawpad.ringlist.adelete(self.type, self.idx)
              await self.my_viewer.drawpad.set_mask_local(ringlist = [])
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'setbtevent':
        if self.may_write:
          if 'bt_new' in params:
            await self.my_viewer.drawpad.new_ring()
            self.my_viewer.drawpad.make_screen()
            self.my_viewer.drawpad.mask_from_polygons()
        outlist['data'] = 'OK'
        #logger.info('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'mousedown':
        if self.my_viewer.drawpad.edit_active:
          if self.may_write:
            self.my_viewer.drawpad.mousedownhandler(
              round(params['x'] * self.my_viewer.client_dict[self.v_client_nr]['x_scaling']), 
              round(params['y'] * self.my_viewer.client_dict[self.v_client_nr]['y_scaling']), 
            )
        #else:
        #  if self.mycamitem.mycam and self.mycamitem.mycam.myptz:
        #    self.mycamitem.inqueue.put((
        #      'ptz_mdown', 
        #      params['x'] * self.my_viewer.client_dict[self.v_client_nr]['x_scaling'], 
        #      params['y'] * self.my_viewer.client_dict[self.v_client_nr]['y_scaling'], 
        #    ))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'mouseup':
        if self.my_viewer.drawpad.edit_active:
          if self.may_write:
            await self.my_viewer.drawpad.mouseuphandler(
              round(params['x'] * self.my_viewer.client_dict[self.v_client_nr]['x_scaling']), 
              round(params['y'] * self.my_viewer.client_dict[self.v_client_nr]['y_scaling']), 
            )
          self.myitem.shared_mem.write_mask(self.my_viewer.drawpad.mask) 
        #else:
        #  if self.mycamitem.mycam and self.mycamitem.mycam.myptz:
        #    self.mycamitem.inqueue.put(
        #      ('ptz_mup', params['x']/self.scaling, params['y']/self.scaling)
        #    )
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'mousemove':
        if self.my_viewer.drawpad.edit_active:
          if self.may_write:
            self.my_viewer.drawpad.mousemovehandler(
              round(params['x'] * self.my_viewer.client_dict[self.v_client_nr]['x_scaling']), 
              round(params['y'] * self.my_viewer.client_dict[self.v_client_nr]['y_scaling']), 
            )
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)	

      elif params['command'] == 'dblclick':
        if self.may_write:
          await self.my_viewer.drawpad.dblclickhandler(
            round(params['x'] * self.my_viewer.client_dict[self.v_client_nr]['x_scaling']), 
            round(params['y'] * self.my_viewer.client_dict[self.v_client_nr]['y_scaling']), 
          )
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
        outlist['data'] = streams_redis.get_ptz_pos(self.idx)
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
          self.myitem.shared_mem.write_1_meta(
            'nr_of_cond_ed', 
            self.myitem.shared_mem.read_1_meta('nr_of_cond_ed') + 1, 
          )
          self.myitem.shared_mem.write_1_meta('last_cond_ed', int(params['reaction']))
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'cond_close':
        if self.may_write:
          self.myitem.shared_mem.write_1_meta(
            'nr_of_cond_ed', 
            max(self.myitem.shared_mem.read_1_meta('nr_of_cond_ed') - 1, 0),  
          )
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.safe_send(outlist)		

      elif params['command'] == 'get_all_conditions':
        result = {1:[], 2:[], 3:[], 4:[], 5:[]}
        condition_lines = evt_condition.objects.filter(eventer_id=self.idx)
        async for item in condition_lines:
          result[item.reaction].append(model_to_dict(item)) 
        outlist['data'] = result
        #logger.info('--> ' + str(outlist))
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

      elif params['command'] == 'save_conditions':
        if self.may_write:
          self.myitem.eve_worker.inqueue.put((
            'save_conditions', params['reaction'], params['conditions']))
          cond_dict = json.loads(params['conditions'])
          conditionlines = evt_condition.objects.filter(
            eventer_id=self.dbline.id, 
            reaction=params['reaction'], 
          )
          async for item in conditionlines:
            await item.adelete()
          for item in cond_dict:
            db_line = evt_condition(
              eventer_id = self.dbline.id,
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
          if params['itemid'] in viewables and 'stream' in viewables[params['itemid']]:
            await viewables[params['itemid']]['stream'].stop()
          streamline = await stream.objects.aget(id=params['itemid'])
          streamline.active = False
          await streamline.asave(update_fields=(("active"), ))
          outlist['data'] = 'OK'
        else:
          outlist['data'] = 'No Access'
        #logger.info('--> ' + str(outlist))
        await self.safe_send(outlist)	
    except:
      logger.error('Error in consumer: ' + logname + ' (oneitem)')
      logger.error(format_exc())
