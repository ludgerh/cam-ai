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

c_event.py V2.1.0 03.03.2024
"""

import numpy as np
import cv2 as cv
from datetime import datetime
from random import randint
from os import path, makedirs
from time import sleep, time
from threading import Thread
from collections import OrderedDict
from traceback import format_exc
from django.db import connection
from django.conf import settings
from django.utils import timezone
from django.db.utils import OperationalError
from .models import event, event_frame, school
from tools.l_tools import ts2filename, uniquename, np_mov_avg, djconf
from tools.l_smtp import l_smtp
from tools.l_crypt import l_crypt
from tools.tokens import maketoken
from schools.c_schools import get_taglist
from streams.models import stream

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
  crypt = None

  def __init__(self, tf_worker, tf_w_index, frame, margin, eventer_dbl, idx, logger):
    super().__init__()
    self.id = idx
    self.tf_worker = tf_worker
    self.eventer_id = eventer_dbl.id
    self.eventer_name = eventer_dbl.name
    self.tf_w_index = tf_w_index
    self.xmax = eventer_dbl.cam_xres - 1
    self.ymax = eventer_dbl.cam_yres - 1
    self.margin = margin
    self.number_of_frames = djconf.getconfigint('frames_event', 32)
    self.isrecording = False
    self.goes_to_school = False
    self.to_email = ''
    self.ts = None
    self.savename = ''
    self.schoolnr = eventer_dbl.eve_school.id
    self.dbline = event()
    self.dbline.camera = eventer_dbl
    self.dbline.start=timezone.make_aware(datetime.fromtimestamp(time()))
    self.tag_list = get_taglist(self.schoolnr)
    self.start = frame[2]
    self.end = frame[2]
    self.append(max(0, frame[3] - margin))
    self.append(min(self.xmax, frame[4] + margin))
    self.append(max(0, frame[5] - margin))
    self.append(min(self.ymax, frame[6] + margin))
    self.append([frame[7]]) #Predictions
    self.logger = logger
    self.frames = OrderedDict([(0, frame)])
    self.last_frame_index = 1
    self.shrink_factor = eventer_dbl.eve_shrink_factor
    self.focus_max = np.max(frame[7][1:])
    self.focus_time = frame[2]
    self.dbline.camera = eventer_dbl
    self.check_out_ts = None
    if c_event.crypt is None:
      if self.dbline.camera.encrypted:
        if self.dbline.camera.crypt_key:
          c_event.crypt = l_crypt(key=self.dbline.camera.crypt_key)
        else:
          c_event.crypt = l_crypt()
          self.dbline.camera.crypt_key = c_event.crypt.key
          self.dbline.camera.save(update_fields=['crypt_key'])

  def add_frame(self, frame):
    s_factor = self.shrink_factor
    if (frame[3] - self.margin) <= self[0]:
      self[0] = max(0, frame[3] - self.margin)
    else:
      self[0] = round(((frame[3] - self.margin) * s_factor + self[0]) 
        / (s_factor+1.0))
    if (frame[4] + self.margin) >= self[1]:
      self[1] = min(self.xmax, frame[4] + self.margin)
    else:
      self[1] = round(((frame[4] + self.margin) * s_factor + self[1]) 
        / (s_factor+1.0))
    if (frame[5] - self.margin) <= self[2]:
      self[2] = max(0, frame[5] - self.margin)
    else:
      self[2] = round(((frame[5] - self.margin) * s_factor + self[2]) 
        / (s_factor+1.0))
    if (frame[6] + self.margin) >= self[3]:
      self[3] = min(self.ymax, frame[6] + self.margin)
    else:
      self[3] = round(((frame[6] + self.margin) * s_factor + self[3]) 
        / (s_factor+1.0))
    self.end = frame[2]
    self[4].append(frame[7]) 
    self.frames[self.last_frame_index] = frame
    self.last_frame_index += 1
    if (new_max := np.max(frame[7][1:])) > self.focus_max:
      self.focus_max = new_max
      self.focus_time = frame[2]

  def merge_frames(self, the_other_one):
    self.frames = {**self.frames, **the_other_one.frames}
    self.frames = OrderedDict(sorted(self.frames.items(), key=lambda x: x[1][2]))
    if the_other_one.focus_max > self.focus_max:
      self.focus_max = the_other_one.focus_max
      self.focus_time = the_other_one.focus_time

  def pred_read(self, radius=3, max=None, ave=None, last=None):
    result2 = np.zeros((len(self.tag_list)), np.float32)
    if self[4]:
      result1 = np.vstack(self[4])
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
      resolve_rules(cond_dict[2],  self.frames[x][7])
        or resolve_rules(cond_dict[3], self.frames[x][7])
        or resolve_rules(cond_dict[4],  self.frames[x][7])
    )] 
    if len(sortindex) > outlength:
      sortindex.sort(key=lambda x: np.max(self.frames[x][7][1:]), reverse=True) #prediction
      sortindex = sortindex[:outlength]
      sortindex.sort(key=lambda x: self.frames[x][2]) #timestamp
    self.frames = OrderedDict([(x, self.frames[x]) for x in sortindex])

  def save(self, cond_dict):
    #print('*** Saving Event:', self.id)
    self.frames_filter(self.number_of_frames, cond_dict)
    frames_to_save = self.frames.values()
    self.dbline.p_string = (self.eventer_name+'('+str(self.eventer_id)+'): '
      + self.p_string())
    self.dbline.start=timezone.make_aware(datetime.fromtimestamp(self.start))
    self.dbline.end=timezone.make_aware(datetime.fromtimestamp(self.end))
    self.dbline.xmin=self[0]
    self.dbline.xmax=self[1]
    self.dbline.ymin=self[2]
    self.dbline.ymax=self[3]
    self.dbline.numframes=len(frames_to_save)
    self.dbline.done = not self.goes_to_school
    while True:
      try:
        self.dbline.save()
        break
      except OperationalError:
        connection.close()
    self.mailimages = []
    for item in frames_to_save:
      pathadd = str(self.dbline.camera.id)+'/'+str(randint(0,99))
      if not path.exists(schoolpath+pathadd):
        makedirs(schoolpath+pathadd)
      filename = uniquename(schoolpath, pathadd+'/'+ts2filename(item[2], 
        noblank=True), 'bmp')
      bmp_data =  cv.imencode('.bmp', item[1])[1].tobytes() 
      if c_event.crypt is not None:
        bmp_data = c_event.crypt.encrypt(bmp_data)
      with open(schoolpath+filename, "wb") as file:
        file.write(bmp_data)
      frameline = event_frame(
        time = timezone.make_aware(datetime.fromtimestamp(item[2])),
        name = filename,
        encrypted = c_event.crypt is not None,
        x1 = item[3],
        x2 = item[4],
        y1 = item[5],
        y2 = item[6],
        event = self.dbline,
      )
      frameline.save()
      self.mailimages.append(frameline.id)
    if len(self.to_email) > 0:
      self.send_emails()

  def smtp_send_mail(self, mysmtp, receiver):
    count = 0
    while count < 5:
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
        html_text += ('<a href="' + clienturl + 'schools/getbigmp4/' 
          + str(self.dbline.id) + '/')
        html_text += str(mytoken[0]) + '/' + mytoken[1] + '/video.html' 
        html_text += '" target="_blank">'
        html_text += ('<img src="' + clienturl + 'eventers/eventjpg/' 
          + str(self.dbline.id) + '/')
        html_text += str(mytoken[0]) + '/' + mytoken[1] + '/video.jpg'
        html_text += '" style="width: 400px; height: auto"</a> <br>\n'
      html_text += 'Here are the images: <br> \n'
      for item in self.mailimages:
        html_text += '<a href="' + clienturl + 'schools/getbigbmp/0/' + str(item) + '/'
        html_text += str(mytoken[0]) + '/' + mytoken[1] + '/' 
        html_text += '" target="_blank">'
        html_text += ('<img src="' + clienturl + 'schools/getbmp/0/' + str(item) 
          + '/3/1/200/200/')
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
      Thread(target=self.smtp_send_mail, name='SMTPSendThread', 
        args=(mysmtp, receiver,)).start()

