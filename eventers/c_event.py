# Copyright (C) 2023 by the CAM-AI authors, info@cam-ai.de
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

import numpy as np
from multiprocessing import Lock
import cv2 as cv
from datetime import datetime
from random import choice, randint
from os import path, makedirs
from concurrent import futures
from time import sleep, time
from threading import Thread
from collections import OrderedDict
from traceback import format_exc
from django.db import connection
from django.conf import settings
from django.utils import timezone
from django.db.utils import OperationalError
from .models import event, event_frame, school
from tools.l_tools import ts2filename, uniquename, randomfilter, np_mov_avg, djconf
from tools.l_smtp import l_smtp
from tools.tokens import maketoken
from schools.c_schools import get_taglist

datapath = djconf.getconfig('datapath', 'data/')
schoolpath = djconf.getconfig('schoolframespath', datapath + 'schoolframes/')
clienturl = settings.CLIENT_URL
if not path.exists(schoolpath):
  makedirs(schoolpath)

def resolve_rules(conditions, predictions):
  if predictions is None:
    return(False)
  if len(conditions) > 0:
    cond_str = '' 
    for item in conditions:
      if cond_str:
        if item['and_or'] == 1:
          cond_str += ' and '
        else:
          cond_str += ' or '
      if item['bracket'] > 0:
        cond_str += '(' * item['bracket']


      if item['c_type'] == 1:
        item_result = True
      elif item['c_type'] == 2:
        count = 0
        item_result = False
        for prediction in predictions:
          if prediction >= item['y']:
            count += 1
            if count >= item['x']:
              item_result = True
              break
      elif item['c_type'] == 3:
        count = 0
        item_result = False
        for prediction in predictions:
          if prediction < item['y']:
            count += 1
            if count >= item['x']:
              item_result = True
              break
      elif item['c_type'] == 4:
        item_result = (predictions[item['x']] >= item['y'])
      elif item['c_type'] == 5:
        item_result = (predictions[item['x']] < item['y'])
      elif item['c_type'] == 6:
        myprediction = predictions[item['x']]
        count = 0
        item_result = True
        for prediction in predictions:
          if prediction > myprediction:
            count += 1
            if count >= item['y']:
              item_result = False
              break
      cond_str += str(item_result)


      if item['bracket'] < 0: 
        cond_str += ')' * (-1 * item['bracket'])
    return(eval(cond_str))
  else:
    return(False)


class c_event(list):

  def __init__(self, tf_worker, tf_w_index, frame, margin, xmax, ymax, 
      schoolnr, eventer_id, eventer_name, logger):
    super().__init__()
    self.tf_worker = tf_worker
    self.eventer_id = eventer_id
    self.eventer_name = eventer_name
    self.tf_w_index = tf_w_index
    self.frames_lock = Lock()
    self.number_of_frames = djconf.getconfigint('frames_event', 32)
    self.isrecording = False
    self.goes_to_school = False
    self.to_email = ''
    self.status = 0
    self.ts = None
    self.savename = ''
    self.schoolnr = schoolnr
    self.dbline = event()
    self.dbline.start=timezone.make_aware(datetime.fromtimestamp(time()))
    while True:
      try:
        self.dbline.school = school.objects.get(id=self.schoolnr)
        break
      except OperationalError:
        connection.close()
    xytemp = self.tf_worker.get_xy(self.dbline.school.id, self.tf_w_index)
    self.xdim = xytemp[0]
    self.ydim = xytemp[1]
    self.tag_list = get_taglist(self.schoolnr)
    self.start = frame[2]
    self.end = frame[2]
    self.append(max(0, frame[3] - margin))
    self.append(min(xmax, frame[4] + margin))
    self.append(max(0, frame[5] - margin))
    self.append(min(ymax, frame[6] + margin))
    self.append(False)
    self.logger = logger
    #self.logger.info('***** Client-Url:' + clienturl)
    index = self.get_new_frame_index(frame[2], True)
    with self.frames_lock:
      self.frames = OrderedDict([(index, [frame, None, 0.0])])
    while True:
      try:
        self.dbline.save()
        break
      except OperationalError:
        connection.close()
    self.focus_max = 0.0
    self.make_predictions()
    self.focus_time = frame[2]

  def get_new_frame_index(self, timestamp, first=False):
    index = (round(timestamp * 10000000.0) % 36000000000)
    if not first:
      while index in self.frames:
        index += 1
    return(index)


  def make_predictions(self):
    ts1 = time()
    while True:
      with self.frames_lock:
        framescopy = self.frames.copy()
      frames_to_process = [x for x in framescopy if framescopy[x][2] <= 0.0]
      if frames_to_process and ((time() - ts1) < 1.0):
        imglist = []
        frame_idxs = []
        for i in frames_to_process:
          if i in self.frames:
            self.frames[i][2] = 0.1
            np_image = cv.cvtColor(self.frames[i][0][1], cv.COLOR_BGR2RGB)
            imglist.append(np_image)
            frame_idxs.append(i)
        if self.tf_w_index is not None:
          self.tf_worker.ask_pred(
            self.schoolnr, 
            imglist, 
            self.tf_w_index,
            frame_idxs,
            self.dbline.id,
          )
      else:       
        break

  def set_pred(self, frame, prediction):
    if (self.tf_w_index is None):
      sleep(djconf.getconfigfloat('short_brake', 0.01))
    else:
        if frame in self.frames:
          self.frames[frame][1] = prediction
          self.frames[frame][2] = np.max(prediction[1:])
          if self.frames[frame][2] >= self.focus_max:
            self.focus_max = self.frames[frame][2]
            self.focus_time = self.frames[frame][0][2]

  def add_frame(self, frame, schoolnr):
    self.schoolnr = schoolnr
    index = self.get_new_frame_index(frame[2])
    with self.frames_lock:
      self.frames[index] = [frame, None, 0.0]
    self.make_predictions()

  def merge_frames(self, the_other_one):
    with self.frames_lock:
      self.frames = {**self.frames, **the_other_one.frames}
      if the_other_one.focus_max > self.focus_max:
        self.focus_max = the_other_one.focus_max
        self.focus_time = the_other_one.focus_time

  def pred_read(self, radius=3, max=None, ave=None, last=None):
    result2 = np.zeros((len(self.tag_list)), np.float32)
    with self.frames_lock:
      result1 = [
        self.frames[x][1] for x in self.frames if self.frames[x][1] is not None
      ]
    if result1:
      result1 = np.vstack(result1)
      if radius > 0:
        result1 = np_mov_avg(result1, radius)
      if max is not None:
        result2 += np.max(result1, axis=0) * max
      if ave is not None:
        result2 += np.average(result1, axis=0) * ave
      if last is not None:
        result2 += result1[-1] * last
      return(np.clip(result2, 0.0, 1.0))
    else:
      return(result2)

  def pred_is_done(self, ts):
    with self.frames_lock:
      framescopy = self.frames.copy()
    for item in framescopy.items():
      if ((item[0] in self.frames) and (item[1][0][2] <= ts) 
          and (item[1][1] is None)):
        if item[1][0][2] < ((time() - 240.0)):
          self.logger.debug('Eventer '+str(self.eventer_id)+': pred_is_done got old frame, age: (sec) ' + str(round(time() - item[1][0][2], 3)))
          with self.frames_lock:
            del self.frames[item[0]]
        elif item[1][0][2] > ((time() - 5.0)):
          return(False)
    return(True)

  def p_string(self):
    predictions = self.pred_read(max=1.0)
    predline = '['
    for i in range(len(self.tag_list)):
      if (predictions[i] >= 0.5):
        if (predline != '['):
          predline += ', '
        predline += str(self.tag_list[i].name)[:3]
    return(predline+']')

  def frames_filter(self, outlength, cond_dict):
    sortindex = [x for x in self.frames if (
      resolve_rules(cond_dict[2],  self.frames[x][1])
        or resolve_rules(cond_dict[3], self.frames[x][1])
        or resolve_rules(cond_dict[4],  self.frames[x][1])
    )]
    if len(sortindex) > outlength:
      sortindex.sort(key=lambda x: self.frames[x][2], reverse=True)
      sortindex = sorted(sortindex[:outlength])
    self.frames = OrderedDict([(x, self.frames[x]) for x in sortindex])

  def save(self, cond_dict):
    try:
      #self.logger.info('*** Saving Event: '+str(self.dbline.id))
      self.frames_filter(self.number_of_frames, cond_dict)
      frames_to_save = self.frames.values()
      self.dbline.p_string=self.eventer_name+'('+str(self.eventer_id)+'): '+self.p_string()
      self.dbline.start=timezone.make_aware(datetime.fromtimestamp(self.start))
      self.dbline.end=timezone.make_aware(datetime.fromtimestamp(self.end))
      self.dbline.xmin=self[0]
      self.dbline.xmax=self[1]
      self.dbline.ymin=self[2]
      self.dbline.ymax=self[3]
      self.dbline.numframes=len(frames_to_save)
      self.dbline.done = not self.goes_to_school
      self.dbline.save()
      self.mailimages = []
      for item in frames_to_save:
        pathadd = str(self.schoolnr)+'/'+str(randint(0,99))
        if not path.exists(schoolpath+pathadd):
          makedirs(schoolpath+pathadd)
        filename = uniquename(schoolpath, pathadd+'/'+ts2filename(item[0][2], 
          noblank=True), 'bmp')
        cv.imwrite(schoolpath+filename, item[0][1])
        frameline = event_frame(
          time=timezone.make_aware(datetime.fromtimestamp(item[0][2])),
          name=filename,
          x1=item[0][3],
          x2=item[0][4],
          y1=item[0][5],
          y2=item[0][6],
          event=self.dbline,
        )
        frameline.save()
        self.mailimages.append(frameline.id)
      if len(self.to_email) > 0:
        self.send_emails()
    except:
      self.logger.error(format_exc())
      self.logger.handlers.clear()

  def smtp_send_mail(self, mysmtp, receiver):
    count = 0
    while True:
      count += 1
      try: 
        mysmtp.login(
          djconf.getconfig('smtp_account'), 
          djconf.getconfig('smtp_password'),
        )
        mysmtp.sendmail(
          djconf.getconfig('smtp_email'), 
          receiver,
        )
        break
      except:
        self.logger.warning('*** ['+str(count)+'] Email sending to: '+receiver+' failed')
        sleep(300)
    mysmtp.logout()
    self.logger.info('*** ['+str(count)+'] Sent email to: '+receiver)

  def send_emails(self):
    self.to_email = self.to_email.split()
    for receiver in self.to_email:
      mytoken = maketoken('EVR', self.dbline.id, receiver)
      mysmtp = l_smtp(
        djconf.getconfig('smtp_mode', 'SSL'), 
        djconf.getconfig('smtp_server', 'localhost'),
      )
      subject = ('#'+str(self.eventer_id) + '(' + self.eventer_name + '): '
        + self.p_string())
      from_name = djconf.getconfig('smtp_name', 'CAM-AI Emailer')
      from_email = djconf.getconfig('smtp_email')
      to_email = receiver
      plain_text = 'Hello CAM-AI user,\n' 
      plain_text += 'We had some movement.\n'  
      if self.savename:
        plain_text += 'Here is the movie: \n' 
        plain_text += clienturl + 'schools/getbigmp4/' + str(self.dbline.id) + '/'
        plain_text += str(mytoken[0]) + '/' + mytoken[1] + '/video.html \n' 
      plain_text += 'Here are the images: \n'  
      for item in self.mailimages:
        plain_text += clienturl + 'schools/getbmp/0/' + str(item) + '/3/1/200/200/'
        plain_text += str(mytoken[0]) + '/' + mytoken[1] + '/ \n' 
      html_text = '<html><body><p>Hello CAM-AI user, <br>\n' 
      html_text += 'We had some movement. <br> \n' 
      if self.savename:
        html_text += '<br>Here is the movie (click on the image): <br> \n' 
        html_text += '<a href="' + clienturl + 'schools/getbigmp4/' + str(self.dbline.id) + '/'
        html_text += str(mytoken[0]) + '/' + mytoken[1] + '/video.html' 
        html_text += '" target="_blank">'
        html_text += '<img src="' + clienturl + 'eventers/eventjpg/' + str(self.dbline.id) + '/'
        html_text += str(mytoken[0]) + '/' + mytoken[1] + '/video.jpg'
        html_text += '" style="width: 400px; height: auto"</a> <br>\n'
      html_text += 'Here are the images: <br> \n'
      for item in self.mailimages:
        html_text += '<a href="' + clienturl + 'schools/getbigbmp/0/' + str(item) + '/'
        html_text += str(mytoken[0]) + '/' + mytoken[1] + '/' 
        html_text += '" target="_blank">'
        html_text += '<img src="' + clienturl + 'schools/getbmp/0/' + str(item) + '/3/1/200/200/'
        html_text += str(mytoken[0]) + '/' + mytoken[1] + '/' 
        html_text += '" style="width: 200px; height: 200px; object-fit: contain"</a> \n'
      html_text += '<br> \n'
      mysmtp.putcontent(
        subject, 
        djconf.getconfig('smtp_name', 'CAM-AI Emailer'),
        djconf.getconfig('smtp_email'), 
        receiver,
        plain_text,
        html_text,)
      Thread(target=self.smtp_send_mail, name='SMTPSendThread', args=(mysmtp, receiver,)).start()

