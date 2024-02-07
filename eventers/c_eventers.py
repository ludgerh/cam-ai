# Copyright (C) 2024 by the CAM-AI team, info@cam-ai.de
# More information and complete source: https://github.com/ludgerh/cam-ai
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

# c_eventer.py V1.1.3 21.01.2024

import cv2 as cv
import json
import numpy as np
from os import remove, path, nice, environ
from math import inf
from shutil import copyfile
from traceback import format_exc
from logging import getLogger
from setproctitle import setproctitle
from collections import deque
from time import time, sleep
from threading import Thread
from multiprocessing import Process, Lock
from subprocess import Popen, run
from django.forms.models import model_to_dict
from django.db import connection
from django.db.utils import OperationalError
from tools.l_tools import djconf
from tools.c_logger import log_ini
from tools.c_tools import hasoverlap, rect_btoa
from viewers.c_viewers import c_viewer
from l_buffer.l_buffer import l_buffer
from tf_workers.c_tfworkers import tf_workers
from tf_workers.models import school
from streams.c_devices import c_device
from streams.models import stream
from schools.c_schools import get_taglist
from .models import evt_condition
from .models import event
from .c_event import c_event, resolve_rules
from .c_alarm import alarm

#from threading import enumerate

class c_eventer(c_device):

  def __init__(self, *args, **kwargs):
    self.type = 'E'
    super().__init__(*args, **kwargs)
    self.mode_flag = self.dbline.eve_mode_flag
    if self.dbline.eve_view:
      self.viewer = c_viewer(self, self.logger)
    else:
      self.viewer = None
    self.tf_worker = tf_workers[school.objects.get(id=self.dbline.eve_school.id).tf_worker.id]
    self.tf_worker.eventer = self
    self.dataqueue = l_buffer(1, block=True)
    self.detectorqueue = l_buffer()
    self.frameslist = deque()
    self.inserter_ts = 0
    self.buffer_ts = time()
    self.display_ts = 0
    self.nr_of_cond_ed = 0
    self.read_conditions()
    self.tag_list = get_taglist(self.dbline.eve_school.id)
    datapath = djconf.getconfig('datapath', 'data/')
    self.recordingspath = djconf.getconfig('recordingspath', datapath + 'recordings/')
    self.last_display = 0

  def runner(self):
    super().runner()
    self.logname = 'eventer #'+str(self.dbline.id)
    self.logger = getLogger(self.logname)
    log_ini(self.logger, self.logname)
    setproctitle('CAM-AI-Eventer #'+str(self.dbline.id))
    try:
      if self.dbline.eve_gpu_nr_cv:
        environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
        environ["CUDA_VISIBLE_DEVICES"] = str(self.dbline.eve_gpu_nr_cv)
        self.logger.info('**** Eventer running GPU #' + str(self.dbline.eve_gpu_nr_cv))
      self.eventdict = {}
      self.eventdict_lock = Lock()

      self.vid_deque = deque()
      self.vid_str_dict = {}
      self.set_cam_counts()

      self.tf_w_index = self.tf_worker.register()
      self.tf_worker.run_out(self.tf_w_index)

      self.finished = False
      self.do_run = True
      self.scaling = None

      Thread(target=self.inserter, name='InserterThread').start()
      
      self.webm_lock = Lock()
      self.redis.set('webm_queue:' + str(self.id) + ':start', 0)
      self.redis.set('webm_queue:' + str(self.id) + ':end', 0)
      self.webm_proc = Process(target=self.make_webm).start()
      while self.do_run:
        frameline = self.dataqueue.get()
        if (self.do_run and (frameline is not None) 
            and self.sl.greenlight(self.period, frameline[2])):
          self.run_one(frameline) 
        else:
          sleep(djconf.getconfigfloat('short_brake', 0.1))
      self.dataqueue.stop()
      with self.eventdict_lock:
        for item in self.eventdict.values():
          event.objects.get(id=item.dbline.id).delete()
      self.finished = True
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()
    self.logger.info('Finished Process '+self.logname+'...')
    self.logger.handlers.clear()
    self.tf_worker.stop_out(self.tf_w_index)
    self.tf_worker.unregister(self.tf_w_index)
    #for thread in enumerate(): 
    #  print(thread)

  def in_queue_handler(self, received):
    try:
      if super().in_queue_handler(received):
        return(True)
      else:
        if (received[0] == 'new_video'):
          self.vid_deque.append(received[1:])
          while True:
            if self.vid_deque and (time() - self.vid_deque[0][2]) > 300:
              listitem = self.vid_deque.popleft()
              try:
                remove(self.recordingspath + listitem[1])
              except FileNotFoundError:
                self.logger.warning('c_eventers.py:new_video - Delete did not find: '
                  + self.recordingspath + listitem[1])
            else:
              break
        elif (received[0] == 'purge_videos'):
          for item in self.vid_deque.copy():
            try:
              remove(self.recordingspath + item[1])
            except FileNotFoundError:
              self.logger.warning('c_eventers.py:purge_videos - Delete did not find: '
                + self.recordingspath + item[1])
          self.vid_deque.clear()
        elif (received[0] == 'set_fpslimit'):
          self.dbline.eve_fpslimit = received[1]
          if received[1] == 0:
            self.period = 0.0
          else:
            self.period = 1.0 / received[1]
        elif (received[0] == 'set_margin'):
          self.dbline.eve_margin = received[1]
        elif (received[0] == 'set_event_time_gap'):
          self.dbline.eve_event_time_gap = received[1]
        elif (received[0] == 'set_school'):
          self.dbline.eve_school = school.objects.get(id=received[1])
        elif (received[0] == 'set_alarm_email'):
          self.dbline.eve_alarm_email = received[1]
        elif (received[0] == 'cond_open'):
          self.nr_of_cond_ed += 1
          self.last_cond_ed = received[1]
        elif (received[0] == 'cond_close'):
          self.nr_of_cond_ed = max(0, self.nr_of_cond_ed - 1)
        elif (received[0] == 'new_condition'):
          self.cond_dict[received[1]].append(received[2])
          self.set_cam_counts()
        elif (received[0] == 'del_condition'):
          self.cond_dict[received[1]] = [item 
            for item in self.cond_dict[received[1]] 
            if item['id'] != received[2]]
          self.set_cam_counts()
        elif (received[0] == 'save_condition'):
          for item in self.cond_dict[received[1]]:
            if item['id'] == received[2]:
	            item['c_type'] = received[3]
	            item['x'] = received[4]
	            item['y'] = received[5]
	            break
          self.set_cam_counts()
        elif (received[0] == 'save_conditions'):
          self.cond_dict[received[1]] = json.loads(received[2])
          self.set_cam_counts()
        elif (received[0] == 'setdscrwidth'):
          self.scrwidth = received[1]
          self.scaling = None
        else:
          return(False)
        return(True)
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def run_one(self, frame):
    #ts1 = time()
    if (not self.redis.view_from_dev('E', self.dbline.id)):
      if self.frameslist:
        self.frameslist.clear()
      sleep(djconf.getconfigfloat('long_brake', 1.0))
    else:
      if (frame is None) or (len(self.frameslist) >= 100):
        return(None)
      myframe = frame[1]
      
      if self.scaling is None:
        if myframe.shape[1] > self.scrwidth:
          self.scaling = self.scrwidth / myframe.shape[1]
        else:
          self.scaling = 1.0  
        self.linewidth = round(4.0 / self.scaling)
        self.textheight = round(0.51 / self.scaling)
        self.textthickness = round(2.0 / self.scaling)
      frame = (frame[0], myframe, frame[2])
      frameplusevents = {}
      frameplusevents['frame'] = frame
      frameplusevents['events'] = []
      with self.eventdict_lock:
        for i in self.eventdict:
          if self.eventdict[i].status == 0:
            frameplusevents['events'].append((
              i, 
              self.eventdict[i].end, 
              self.eventdict[i][:4]
            ))
      self.frameslist.append(frameplusevents)
      self.display_events()

  def read_conditions(self):
    self.cond_dict = {1:[], 2:[], 3:[], 4:[], 5:[]}
    condition_lines = evt_condition.objects.filter(eventer_id=self.dbline.id)
    for item in condition_lines:
      self.cond_dict[item.reaction].append(model_to_dict(item))

  def merge_events(self):
    while True:
      changed = False
      with self.eventdict_lock:
        for i in self.eventdict:
          if (i in self.eventdict) and (self.eventdict[i].status == 0):
            for j in self.eventdict:
              if ((j > i) and (j in self.eventdict) 
                  and (self.eventdict[j].status == 0) 
                  and hasoverlap(self.eventdict[i], self.eventdict[j])):
                self.eventdict[i][0] = min(self.eventdict[i][0], 
                  self.eventdict[j][0])
                self.eventdict[i][1] = max(self.eventdict[i][1], 
                  self.eventdict[j][1])
                self.eventdict[i][2] = min(self.eventdict[i][2], 
                  self.eventdict[j][2])
                self.eventdict[i][3] = max(self.eventdict[i][3], 
                  self.eventdict[j][3])
                self.eventdict[i].end = max(self.eventdict[i].end, 
                  self.eventdict[j].end)
                self.eventdict[j].status = -3
                self.eventdict[i].merge_frames(self.eventdict[j])
                self.eventdict[j].isrecording = False
                self.eventdict[j].goes_to_school = False
                changed = True
      if not changed:
        break

  def display_events(self):
    try:
      while len(self.frameslist) > 0:
        myframeplusevents = self.frameslist.popleft()
        all_done = True
        for item in myframeplusevents['events']:
          if ((item[0] in self.eventdict) 
              and (self.eventdict[item[0]].status >= -2)):
            myevent = self.eventdict[item[0]]
            if (not myevent.pred_is_done(ts=item[1])):
              all_done = False
              break
        if all_done:
          frame = myframeplusevents['frame']
          newimage = frame[1].copy()
          for i in myframeplusevents['events']:
            if i[0] in self.eventdict:
              item = self.eventdict[i[0]]
              if self.eventdict[i[0]].status >= -2:
                itemold = i[2]
                predictions = item.pred_read(max=1.0)
                if self.dbline.eve_all_predictions or (self.nr_of_cond_ed > 0):
                  if self.nr_of_cond_ed <= 0:
                    self.last_cond_ed = 1
                  if resolve_rules(self.cond_dict[self.last_cond_ed], predictions):
                    colorcode= (0, 0, 255)
                  else:
                    colorcode= (0, 255, 0)
                  displaylist = [(j, predictions[j]) for j in range(10)]
                  displaylist.sort(key=lambda x: -x[1])
                  cv.rectangle(newimage, rect_btoa(itemold), colorcode, self.linewidth)
                  if itemold[2] < (self.dbline.cam_yres - itemold[3]):
                    y0 = itemold[3] + 30 * self.textheight
                  else:
                    y0 = itemold[2] - 70 * self.textheight
                  for j in range(3):
                    cv.putText(newimage, 
                      self.tag_list[displaylist[j][0]].name[:3]
                      +' - '+str(round(displaylist[j][1],2)), 
                      (itemold[0]+2, y0 + j * 30 * self.textheight), 
                      cv.FONT_HERSHEY_SIMPLEX, self.textheight, colorcode, 
                      self.textthickness, cv.LINE_AA)
                else:
                  imax = -1
                  pmax = -1
                  for j in range(1,len(predictions)):
                    if predictions[j] >= 0.0:
                      if predictions[j] > pmax:
                        pmax = predictions[j]
                        imax = j
                  if resolve_rules(self.cond_dict[1], predictions):
                    cv.rectangle(newimage, rect_btoa(itemold), (255, 0, 0), 
                      self.linewidth)
                    cv.putText(newimage, self.tag_list[imax].name[:3], 
                      (itemold[0]+10, itemold[2]+30), 
                      cv.FONT_HERSHEY_SIMPLEX, self.textheight, (255, 0, 0), 
                        self.textthickness, cv.LINE_AA)
              self.last_display = frame[2]
          if self.dbline.eve_view:
            fps = self.som.gettime()
            if fps:
              self.dbline.eve_fpsactual = fps
              while True:
                try:
                  stream.objects.filter(id = self.dbline.id).update(eve_fpsactual = fps)
                  break
                except OperationalError:
                  connection.close()
              self.redis.fps_to_dev('E', self.dbline.id, fps)
            self.viewer.inqueue.put(data=(3, newimage, frame[2]))
        else:
          self.frameslist.appendleft(myframeplusevents)
          break
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def make_webm(self):
    setproctitle('CAM-AI-Eventer(WEBM) #'+str(self.dbline.id))
    while True:
      with self.webm_lock:
        the_start = self.redis.get('webm_queue:' + str(self.id) + ':start')
        if the_start == b'stop':
          return()
        else:
          the_start = int(the_start)  
        the_end = int(self.redis.get('webm_queue:' + str(self.id) + ':end'))
        if (the_end > 0) and (the_end == the_start):
          self.redis.set('webm_queue:' + str(self.id) + ':start', 0)
          self.redis.set('webm_queue:' + str(self.id) + ':end', 0)
      if the_end > the_start:
        the_start += 1
        savepath = (self.redis.get('webm_queue:' + str(self.id) + ':item:' 
          + str(the_start)).decode("utf-8"))
        self.redis.delete('webm_queue:' + str(self.id) + ':item:' + str(the_start))
        self.redis.set('webm_queue:' + str(self.id) + ':start', str(the_start))
        niceness = nice(0)
        nice(19 - niceness)
        myts = time()
        run([
          'ffmpeg', 
          '-v', 'fatal', 
          '-i', savepath, 
          '-crf', '51', #0 = lossless, 51 = very bad
          '-vf', 'scale=500:-1',
          savepath[:-4]+'.webm'
        ])
        self.logger.info('WEBM-Conversion: E' + str(self.id) + ' ' 
          + str(round(time() - myts)) + ' sec')
      else:
        sleep(djconf.getconfigfloat('long_brake', 5.0))
    

  def check_events(self, idict):
    try:
      myevent = self.eventdict[idict]
      if (((myevent.end < (time() 
            - self.dbline.eve_event_time_gap)) 
          or (myevent.end > (myevent.start 
            + 180.0))) 
          and (not myevent.ts)):
        myevent.ts = myevent.end
      if (myevent.ts 
          and myevent.pred_is_done(ts = myevent.ts)):
        predictions = myevent.pred_read(max=1.0)
        myevent.goes_to_school = resolve_rules(self.cond_dict[2], 
          predictions)
        myevent.isrecording = (
          myevent.isrecording or resolve_rules(self.cond_dict[3],
            predictions))
        if resolve_rules(self.cond_dict[4], predictions):
          myevent.to_email = self.dbline.eve_alarm_email
        else:
          myevent.to_email = ''
        if resolve_rules(self.cond_dict[5], predictions):
          alarm(self.dbline.id, self.dbline.name, predictions, 
            self.dbline.eve_school.id, self.logger)
        if (myevent.goes_to_school 
            or myevent.isrecording
            or myevent.to_email):
          if myevent.isrecording:
            if (self.vid_deque and (myevent.end <= (self.vid_deque[-1][2] - self.dbline.cam_latency))):
              my_vid_list = []
              my_vid_str = ''
              my_vid_start = None
              for i in range(len(self.vid_deque)):
                if (myevent.start <= self.vid_deque[i][2]):
                  if not my_vid_start:
                    my_vid_start = (self.vid_deque[i][2] - 10.5) #10 seconds video length plus average trigger delay from checkmp4
                  my_vid_end = self.vid_deque[i][2]
                  my_vid_list.append(self.vid_deque[i][1])
                  my_vid_str += str(self.vid_deque[i][0])
              vid_offset = myevent.focus_time - my_vid_start
              vid_offset = max(vid_offset, 0.0)
              if my_vid_str in self.vid_str_dict:
                myevent.savename=self.vid_str_dict[my_vid_str]
                isdouble = True
              else:
                myevent.savename = ('E_'
                  +str(myevent.dbline.id).zfill(12)+'.mp4')
                savepath = (self.recordingspath + myevent.savename)
                if len(my_vid_list) == 1: 
                  copyfile(self.recordingspath + my_vid_list[0], savepath)
                else:
                  tempfilename = (self.recordingspath + 'T_'
                    + str(myevent.dbline.id).zfill(12)+'.temp')
                  with open(tempfilename, 'a') as f1:
                    for line in my_vid_list:
                      f1.write('file ' + path.abspath(self.recordingspath + line) + '\n')
                  run(['ffmpeg', 
                    '-f', 'concat', 
                    '-safe', '0', 
                    '-v', 'fatal', 
                    '-i', tempfilename, 
                    '-codec', 'copy', 
                    savepath])
                  remove(tempfilename)
                self.vid_str_dict[my_vid_str] = myevent.savename
                isdouble = False
              myevent.dbline.videoclip = myevent.savename[:-4]
              myevent.dbline.double = isdouble
              myevent.dbline.save()
              if not isdouble:
                run([
                  'ffmpeg', 
                  '-ss', str(vid_offset), 
                  '-v', 'fatal', 
                  '-i', savepath, 
                  '-vframes', '1', 
                  '-q:v', '2', 
                  savepath[:-4]+'.jpg'
                ])
                with self.webm_lock:
                  the_end = int(self.redis.get('webm_queue:' + str(self.id) + ':end'))
                  the_end += 1
                  self.redis.set('webm_queue:' + str(self.id) + ':item:' + str(the_end), savepath)
                  self.redis.set('webm_queue:' + str(self.id) + ':end', str(the_end))
              myevent.status = min(-2, 
                myevent.status)
            else:  
              myevent.status = -1
          else:
            myevent.status  = min(-2, 
              myevent.status)
        else:
          myevent.status  = min(-2, 
            myevent.status)
      if ((myevent.status == -2)
          and (myevent.goes_to_school 
          or myevent.isrecording
          or myevent.to_email)):
        myevent.save(self.cond_dict) 
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def inserter(self):
    try:
      while (not self.tf_worker.check_ready(self.tf_w_index)):
        sleep(djconf.getconfigfloat('long_brake', 1.0))
      local_ts = time()
      while self.do_run:
        if (time() - local_ts) > 1.0:
          local_ts = time()
          deletelist = []
          with self.eventdict_lock:
            for i in self.eventdict:
              myevent = self.eventdict[i]
              if myevent.status <= -2:
                if (myevent.end <= self.last_display) or (not self.redis.view_from_dev('E', self.dbline.id)): 
                  if not (myevent.isrecording 
                      or myevent.goes_to_school
                      or myevent.to_email): 
                    while True:
                      try:
                        event.objects.get(id=myevent.dbline.id).delete()
                        break
                      except OperationalError:
                        connection.close()
                  deletelist.append(i)
              else:
                self.check_events(i)
            for i in deletelist:
              del self.eventdict[i]  
        if self.redis.check_if_counts_zero('E', self.dbline.id):
          sleep(djconf.getconfigfloat('short_brake', 0.1))
        else:
          margin = self.dbline.eve_margin
          if self.detectorqueue.empty():
            frame = None
          else:
            queueresult = self.detectorqueue.get()
            np_image = np.frombuffer(queueresult[0], dtype=np.uint8)
            np_image = np_image.reshape(queueresult[1][5]-queueresult[1][4], queueresult[1][3]-queueresult[1][2], 3)
            frame = (
              queueresult[1][0],
              np_image,
              queueresult[1][1],
              queueresult[1][2],
              queueresult[1][3],
              queueresult[1][4],
              queueresult[1][5],
            )
          if frame:
            if not self.dbline.cam_xres:
              self.dbline.refresh_from_db(fields=['cam_xres', 'cam_yres', ])
            found = None
            with self.eventdict_lock:
              for idict in self.eventdict:
                myevent = self.eventdict[idict]
                if ((myevent.status == 0)
                  and (myevent.dbline.xmax > -1)
                  and (myevent.end > (frame[2] - 
                    self.dbline.eve_event_time_gap))
                  and hasoverlap((frame[3]-margin, frame[4]+margin, 
                    frame[5]-margin, frame[6]+margin), myevent)):
                  found = myevent
                  break
              if found is None:
                myevent = c_event(self.tf_worker, self.tf_w_index, frame, 
                  self.dbline.eve_margin, self.dbline.cam_xres-1, self.dbline.cam_yres-1, 
                  self.dbline.eve_school.id, self.id, self.dbline.name, self.logger)
                self.eventdict[myevent.dbline.id] = myevent
              else: 
                s_factor = 0.1 # user changeable later: 0.0 -> No Shrinking 1.0 50%
                if (frame[3] - margin) <= found[0]:
                  found[0] = max(0, frame[3] - margin)
                else:
                  found[0] = round(((frame[3] - margin) * s_factor + found[0]) 
                    / (s_factor+1.0))
                if (frame[4] + margin) >= found[1]:
                  found[1] = min(self.dbline.cam_xres-1, frame[4] + margin)
                else:
                  found[1] = round(((frame[4] + margin) * s_factor + found[1]) 
                    / (s_factor+1.0))
                if (frame[5] - margin) <= found[2]:
                  found[2] = max(0, frame[5] - margin)
                else:
                  found[2] = round(((frame[5] - margin) * s_factor + found[2]) 
                    / (s_factor+1.0))
                if (frame[6] + margin) >= found[3]:
                  found[3] = min(self.dbline.cam_yres-1, frame[6] + margin)
                else:
                  found[3] = round(((frame[6] + margin) * s_factor + found[3]) 
                    / (s_factor+1.0))
                found.end = frame[2]
                found.add_frame(frame, self.dbline.eve_school.id) 
            self.merge_events()
            self.inserter_ts = frame[2]
          else:  
            sleep(djconf.getconfigfloat('short_brake', 0.1))
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def set_cam_counts(self):
    if any([len(self.cond_dict[x]) for x in range(2,6)]):
      self.add_data_count() #just switch 0 or 1
    else:
      self.take_data_count()
    if self.cond_dict[3]:
      self.add_record_count()
    else:
      self.take_record_count()

  def build_string(self, i):
    if i['c_type'] == 1:
	    result = 'Any movement detected'
    elif  i['c_type'] in {2, 3}:
	    result = str(i['x'])+' predictions are '
    elif i['c_type']  in {4, 5}:
	    result = 'Tag "'+self.tag_list[i['x']].name+'" is '
    elif i['c_type'] == 6:
	    result = ('Tag "'+self.tag_list[i['x']].name+'" is in top '
        +str(round(i['y'])))
    if i['c_type'] in {2,4}:
	    result += 'above or equal '+str(i['y'])
    elif i['c_type'] in {3,5}:
	    result += 'below or equal '+str(i['y'])
    return(result)

  def sort_in_prediction(self, events, frames, predictions):
    for i in range(predictions.shape[0]):
      if events[i] in self.eventdict:
        self.eventdict[events[i]].set_pred(frames[i], predictions[i])

  def stop(self):
    self.redis.set('webm_queue:' + str(self.id) + ':start', 'stop')
    self.dataqueue.stop()
    super().stop()
    #self.run_process.join()
    
