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
import numpy as np
import cv2 as cv
from os import path, makedirs, remove
from shutil import copy
from PIL import Image
from random import randint
from logging import getLogger
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from django.core import serializers
from django.db.models import Q
from django.core.paginator import Paginator
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.hashers import check_password
from tools.l_tools import ts2filename, djconf, uniquename
from tools.djangodbasync import (filterlines, getoneline, savedbline, 
  deldbline, updatefilter, deletefilter, getonelinedict, filterlinesdict,
  countfilter)
from tools.c_logger import log_ini
from access.c_access import access
from access.models import access_control
from schools.c_schools import get_taglist, check_extratags_async
from tf_workers.c_tfworkers import tf_workers
from tf_workers.models import school
from eventers.models import event, event_frame
from trainers.models import trainframe
from users.models import userinfo, archive

logname = 'ws_schoolsconsumers'
logger = getLogger(logname)
log_ini(logger, logname)
classes_list = get_taglist(1)
schoolframespath = djconf.getconfig('schoolframespath', 'data/schoolframes/')
recordingspath = djconf.getconfig('recordingspath', 'data/recordings/')
schoolsdir = djconf.getconfig('schools_dir', 'data/schools/')

#*****************************************************************************
# SchoolDBUtil
#*****************************************************************************

class schooldbutil(AsyncWebsocketConsumer):

  @database_sync_to_async
  def gettags(self, myschool):
    return([line.description for line in get_taglist(myschool)])

  @database_sync_to_async
  def gettrainimages(self, page_nr):
    lines = []
    for line in self.trainpag.page(page_nr):
      if line.made_by is None:
        made_by = ''
      else:
        made_by = line.made_by.username
      lines.append({
      'id' : line.id, 
      'name' : line.name, 
      'made_by' : made_by,
      'cs' : [line.c0,line.c1,line.c2,line.c3,line.c4,line.c5,line.c6,
        line.c7,line.c8,line.c9,],
      'made' : line.made.strftime("%d.%m.%Y %H:%M:%S %Z"),
      })
    return(lines)

  @database_sync_to_async
  def getshortlist(self, page_nr):
    return(list(self.trainpag.get_elided_page_range(page_nr)))

  async def connect(self):
    self.user = self.scope['user']
    if self.user.is_authenticated:
      self.tf_w_index = None
      await self.accept()
    else:
      await self.close()
    self.schoolinfo = None

  async def disconnect(self, close_code):
    if self.tf_w_index is not None:
      self.tf_worker.stop_out(self.tf_w_index)
      self.tf_worker.unregister(self.tf_w_index) 

  async def receive(self, text_data):
    logger.debug('<-- ' + text_data)
    params = json.loads(text_data)['data']

    if ((params['command'] == 'gettags') 
        or self.scope['user'].is_authenticated):
      outlist = {'tracker' : json.loads(text_data)['tracker']}
    else:
      await self.close()

    if params['command'] == 'settrainpag' :
      filterdict = {'school' : params['model']}
      if params['cbnot']:
        if not params['cbchecked']:
          filterdict['checked'] = 0
      else:
        if params['cbchecked']:
          filterdict['checked'] = 1
        else:
          filterdict['checked'] = -1 #Never
      if params['class'] == -2:
        pass
      elif params['class'] == -1:
        for i in range(0,10):
          filterdict['c'+str(i)] = 0
      else:
        filterdict['c'+str(params['class'])] = 1
      allresults = await filterlines(trainframe, filterdict)
      self.trainpag = Paginator(allresults, params['pagesize'])
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))

    if params['command'] == 'gettrainimages' :
      outlist['data'] = await self.gettrainimages(params['page_nr'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))

    if params['command'] == 'getshortlist' :
      result = list(await self.getshortlist(params['page_nr']))
      for i in range(len(result)):
        if not isinstance(result[i], int):
          result[i] = 0
      outlist['data'] = result
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))

    elif params['command'] == 'gettags':

      outlist['data'] = await self.gettags(params['school'])
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))

    elif params['command'] == 'getpredictions':
      if access.check('S', params['school'], self.scope['user'], 'R'):
        imglist = None
        for item in params['idxs']:
          try:
            if params['is_school']:
              framedict = await getonelinedict(event_frame, {'id' : item, }, ['name', 'event'])
              imagepath = schoolframespath + framedict['name']
              if self.schoolinfo is None:
                eventdict = await getonelinedict(event, {'id' : framedict['event'], }, ['school'])
                schooldict = await getonelinedict(school, {'id' : eventdict['school'], }, ['id', 'e_school', 'dir'])
                xytemp = self.tf_worker.get_xy(schooldict['id'], self.tf_w_index)
                self.schoolinfo = {'xdim' : xytemp[0], 'ydim' : xytemp[1], }
            else:
              framedict = await getonelinedict(trainframe, {'id' : item, }, ['name', 'school'])
              if self.schoolinfo is None:
                schooldict = await getonelinedict(school, {'id' : framedict['school'], }, ['id', 'e_school', 'dir'])
                xytemp = self.tf_worker.get_xy(schooldict['id'], self.tf_w_index)
                self.schoolinfo = {'xdim' : xytemp[0], 'ydim' : xytemp[1], 'schooldict' : schooldict, }
              imagepath = self.schoolinfo['schooldict']['dir'] + 'frames/' + framedict['name']
            if imglist is None:
              imglist = []
            np_image = np.array(Image.open(imagepath))
            imglist.append(np_image)
          except FileNotFoundError:
            logger.error('File not found: ' + imagepath)
        self.tf_worker.ask_pred(
          params['school'], 
          imglist, 
          self.tf_w_index,
          [],
          -1,
        )
        predictions = np.empty((0, len(classes_list)), np.float32)
        while predictions.shape[0] < len(imglist):
          predictions = np.vstack((predictions, self.tf_worker.get_from_outqueue(self.tf_w_index)))
        outlist['data'] = predictions.tolist()
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

    elif params['command'] == 'checktrainframe':
      mytrainframe = await getoneline(trainframe, {'id' : params['img'], })
      if access.check('S', mytrainframe.school, self.user, 'W'):
        mytrainframe.checked = True
        await savedbline(mytrainframe, ['checked'])
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

    elif params['command'] == 'deltrainframe':
      trainframedict = await getonelinedict(trainframe, {'id' : params['img'], }, ['name', 'school'])
      if access.check('S', trainframedict['school'], self.user, 'W'):
        await deletefilter(trainframe, {'id' : params['img'], })
        schooldict = await getonelinedict(school, {'id' : trainframedict['school'], }, ['dir'])
        framefile = schooldict['dir'] + 'frames/' + trainframedict['name']
        if path.exists(framefile):
          remove(framefile)
        else:
          logger.warning('deltrainframe - Delete did not find: ' + framefile)
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))

    elif params['command'] == 'checkall':
      if access.check('S', params['school'], self.user, 'W'):
        filterdict = {'school' : params['school']}
        if params['class'] == -2:
          pass
        elif params['class'] == -1:
          for i in range(0,len(classes_list)):
            filterdict['c'+str(i)] = 0
        else:
          filterdict['c'+str(params['class'])] = 1
        filterdict['id__gte'] = params['min_id']
        filterdict['id__lte'] = params['max_id']
        await updatefilter(trainframe, filterdict, {'checked' : 1}, )
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

    elif params['command'] == 'deleteall':
      if access.check('S', params['school'], self.user, 'W'):
        filterdict = {'school' : params['school']}
        if params['class'] == -2:
          pass
        elif params['class'] == -1:
          for i in range(0,10):
            filterdict['c'+str(i)] = 0
        else:
          filterdict['c'+str(params['class'])] = 1
        filterdict['id__gte'] = params['min_id']
        filterdict['id__lte'] = params['max_id']
        if params['cbnot']:
          if params['cbchecked']:
            pass
          else:
            filterdict['checked'] = 0
        else:
          if params['cbchecked']:
            filterdict['checked'] = 1
          else:
            filterdict = None
        if filterdict is not None:
          schooldict = await getonelinedict(school, {'id' : params['school'], }, ['dir'])
          filepath = schooldict['dir']
          list_for_del = await filterlinesdict(trainframe, filterdict)
          await deletefilter(trainframe, filterdict)
          for item in list_for_del:
            framefile = filepath + 'frames/' + item['name']
            if path.exists(framefile):
              remove(framefile)
            else:
              logger.warning('deleteall - Delete did not find: ' + framefile)
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

    elif params['command'] == 'copyall':
      if access.check('S', params['school'], self.user, 'W'):
        filterdict = {'school' : params['school']}
        if params['class'] == -2:
          pass
        elif params['class'] == -1:
          for i in range(0,10):
            filterdict['c'+str(i)] = 0
        else:
          filterdict['c'+str(params['class'])] = 1
        filterdict['id__gte'] = params['min_id']
        filterdict['id__lte'] = params['max_id']
        if params['cbnot']:
          if params['cbchecked']:
            pass
          else:
            filterdict['checked'] = 0
        else:
          if params['cbchecked']:
            filterdict['checked'] = 1
          else:
            filterdict = None
        if filterdict is not None:
          schooldictin = await getonelinedict(school, {'id' : params['school'], }, ['dir'])
          sourcepath = schooldictin['dir']
          schooldictout = await getonelinedict(school, {'id' : 1, }, ['dir'])
          destpath = schooldictout['dir']
          list_for_copy = await filterlinesdict(trainframe, filterdict)
          for item in list_for_copy:
            if not (await check_extratags_async(params['school'], item)):
              destfilename = uniquename(destpath, path.splitext(item['name'])[0], 'bmp')  
              copy(sourcepath + 'frames/' + item['name'], destpath + 'frames/' + destfilename)
              newitem = trainframe(made = item['made'],
                school = 1,
                name = destfilename,
                code = 'NE',
                c0 = item['c0'], c1 = item['c1'], c2 = item['c2'], c3 = item['c3'], 
                c4 = item['c4'], c5 = item['c5'], c6 = item['c6'], c7 = item['c7'], 
                c8 = item['c8'], c9 = item['c9'], 
                checked = False,
                made_by_id = item['made_by'],
              )
              await savedbline(newitem)
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))

    elif params['command'] == 'register_ai':
      self.myschool = int(params['school'])
      if ('logout' in params) and params['logout'] and (self.myschool > 0):
        await self.disconnect(None)
      if self.myschool > 0:
        schooldict = await getonelinedict(school, {'id' : self.myschool, }, ['tf_worker'])
        self.tf_worker = tf_workers[schooldict['tf_worker']]
        self.tf_w_index = self.tf_worker.register()
        self.tf_worker.run_out(self.tf_w_index)
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))

    elif params['command'] == 'getschoolframes':
      framelines = await filterlinesdict(event_frame, {'event__id' : params['event'], }, ['id', 'name', 'time'])
      for item in framelines:
        item['time'] = item['time'].now().strftime('%d.%m.%Y %H:%M:%S')
      outlist['data'] = framelines
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))

    elif params['command'] == 'settags':
      eventdict = await getonelinedict(event, {'id' : params['event'], }, ['id', 'school', 'done'])
      schoolnr = eventdict['school']
      schooldict = await getonelinedict(school, {'id' : schoolnr, }, ['dir'])
      modelpath = schooldict['dir']
      if access.check('S', schoolnr, self.scope['user'], 'W'):
        if not path.exists(modelpath + 'frames/'):
          makedirs(modelpath + 'frames/')
        framelines = await filterlinesdict(event_frame, {'event__id' : params['event'], }, ['id', 'name', 'time', 'trainframe', ])
        i = 0
        for item in framelines:
          pathadd = str(randint(0,99))+'/'
          if not path.exists(modelpath + 'frames/' + pathadd):
            makedirs(modelpath + 'frames/' + pathadd)
          ts = datetime.timestamp(item['time'])
          newname = uniquename(modelpath + 'frames/', pathadd+ts2filename(ts, noblank=True), 'bmp')
          updatedict = {}
          for j in range(10):
            updatedict['c'+str(j)] = params['cblist'][i][j]
          if eventdict['done']:
            await updatefilter(trainframe, {'id' : item['trainframe'], }, updatedict)
          else:
            copy(schoolframespath + item['name'], modelpath + 'frames/' + newname)
            t = trainframe(made=item['time'],
              school=schoolnr,
              name=newname,
              code='NE',
              checked=0,
              made_by_id=self.user.id,
            );
            t.c0=params['cblist'][i][0]
            t.c1=params['cblist'][i][1]
            t.c2=params['cblist'][i][2]
            t.c3=params['cblist'][i][3]
            t.c4=params['cblist'][i][4]
            t.c5=params['cblist'][i][5]
            t.c6=params['cblist'][i][6]
            t.c7=params['cblist'][i][7]
            t.c8=params['cblist'][i][8]
            t.c9=params['cblist'][i][9]
            trainframenr = await savedbline(t)
            await updatefilter(event_frame, {'id' : item['id'], }, {'trainframe' : trainframenr, }) 
          i += 1
        await updatefilter(event, {'id' : eventdict['id'], }, {'done' : True, }) 

      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'delevent':
      try:
        if params['eventnr']:
          eventdicts = await filterlinesdict(event, {'id' : params['eventnr'], }, ['id', 'school', 'videoclip'])
          schoolnr = eventdicts[0]['school']
        else:
          eventdicts = await filterlinesdict(event, {'school__id' : params['schoolnr'], 'done' : True, }, ['id', 'school', 'videoclip'])
          schoolnr =  params['schoolnr']
        if access.check('S', schoolnr, self.scope['user'], 'W'):
          for eitem in eventdicts:
            framelines = await filterlinesdict(event_frame, {'event__id' : eitem['id'], }, ['id', 'name', ])
            for fitem in framelines:
              framefile = schoolframespath + fitem['name']
              if path.exists(framefile):
                remove(framefile)
              else:
                logger.warning('delevent - Delete did not find: ' + framefile)
              await deletefilter(event_frame, {'id' : fitem['id'], })
            if eitem['videoclip']:
              if (await countfilter(event, {'videoclip' : eitem['videoclip'], })) <= 1:
                videofile = recordingspath + eitem['videoclip']
                if path.exists(videofile + '.mp4'):
                  remove(videofile + '.mp4')
                else:
                  logger.warning('delevent - Delete did not find: ' + videofile + '.mp4')
                if path.exists(videofile + '.webm'):
                  remove(videofile + '.webm')
                else:
                  logger.warning('delevent - Delete did not find: ' + videofile + '.webm')
                if path.exists(videofile + '.jpg'):
                  remove(videofile + '.jpg')
                else:
                  logger.warning('delevent - Delete did not find: ' + videofile + '.jpg')
            await deletefilter(event, {'id' : eitem['id'], })
      except event.DoesNotExist:
        logger.warning('delevent - Did not find DB line: ' + str(params['eventnr']))
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))			

    elif params['command'] == 'delitem':
      if params['dtype'] == '0':
        framedict = await getonelinedict(event_frame, {'id' : params['nr_todel'], }, ['id', 'name', 'event'])
        eventdict = await getonelinedict(event, {'id' : framedict['event'], }, ['id', 'school', 'numframes'])
        myschool = eventdict['school']
        if access.check('S', myschool, self.scope['user'], 'W'):
          framefile = schoolframespath + framedict['name']
          if path.exists(framefile):
            remove(framefile)
          else:
            logger.warning('delitem - Delete did not find: ' + framefile)
          await deletefilter(event_frame, {'id' : framedict['id'], })
          await updatefilter(event, {'id' : eventdict['id'], }, {'numframes' : (eventdict['numframes'] - 1), })
      elif params['dtype'] == '1':
        eventdict = await getonelinedict(event, {'id' : int(params['nr_todel']), }, ['id', 'school', 'videoclip'])
        myschool = eventdict['school']
        if access.check('S', myschool, self.scope['user'], 'W'):
          if (await countfilter(event, {'videoclip' : eventdict['videoclip'], })) <= 1:
            videofile = recordingspath + eventdict['videoclip']
            if path.exists(videofile + '.mp4'):
              remove(videofile + '.mp4')
            else:
              logger.warning('delitem - Delete did not find: ' + videofile + '.mp4')
            if path.exists(videofile + '.webm'):
              remove(videofile + '.webm')
            else:
              logger.warning('delitem - Delete did not find: ' + videofile + '.webm')
            if path.exists(videofile + '.jpg'):
              remove(videofile + '.jpg')
            else:
              logger.warning('delitem - Delete did not find: ' + videofile + '.jpg')
          await updatefilter(event, {'id' : eventdict['id'], }, {'videoclip' : '', 'hasarchive' : False, })
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))		

    elif params['command'] == 'remfrschool':
      eventdict = await getonelinedict(event, {'id' : int(params['event']), }, ['id', 'school'])
      myschool = eventdict['school']
      if access.check('S', myschool, self.scope['user'], 'W'):
        await updatefilter(event, {'id' : eventdict['id'], }, {'done' : True, })
      outlist['data'] = 'OK'
      logger.debug('--> ' + str(outlist))
      await self.send(json.dumps(outlist))			

    elif params['command'] == 'setonetag':
      framedict = await getonelinedict(trainframe, {'id' : int(params['img']), }, ['school'])
      if access.check('S', framedict['school'], self.scope['user'], 'W'):
        fieldtochange = 'c'+params['cnt']
        await updatefilter(trainframe, {'id' : int(params['img']), }, {fieldtochange : params['value'], 'made_by_id' : self.user.id, })
        outlist['data'] = 'OK'
        logger.debug('--> ' + str(outlist))
        await self.send(json.dumps(outlist))		

#*****************************************************************************
# SchoolUtil
#*****************************************************************************

class schoolutil(AsyncWebsocketConsumer):		

  async def receive(self, text_data=None, bytes_data=None):
    logger.debug('<-- ' + str(text_data))
    indict=json.loads(text_data)
    if indict['code'] == 'makeschool':
      myclient = await getoneline(client, {'id' : indict['client_nr'], })
      if not check_password(indict['pass'], myclient.hash):
        await self.send(json.dumps(None))
        return()
      newschool = school()
      newschool.name = indict['name']
      await savedbline(newschool)
      result = {'school' : newschool.id, }
      newaccess = access_control()
      newaccess.vtype = 'S'
      newaccess.vid = newschool.id
      newaccess.u_g = 'U'
      newaccess.u_g_nr = indict['user']
      newaccess.r_w = 'R'
      await savedbline(newaccess)
      schooldir = schoolsdir + 'model' + str(newschool.id) + '/'
      try:
        makedirs(schooldir+'frames')
      except FileExistsError:
        logger.warning('Dir already exists: '+schooldir+'frames')
      try:
        makedirs(schooldir+'model')
      except FileExistsError:
        logger.warning('Dir already exists: '+schooldir+'model')
      copy(schoolsdir + 'model1/model/' + newschool.model_type + '.h5',
        schooldir + 'model/' + newschool.model_type + '.h5')
      await updatefilter(school, 
        {'id' : newschool.id, }, 
        {'dir' : schooldir, })
      await self.send(json.dumps(result))				

