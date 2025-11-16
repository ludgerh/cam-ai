"""
Original path: tools/views.py
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

import json
import os
import subprocess
import shutil
import cv2 as cv
from asgiref.sync import async_to_sync
from requests import get as rget
from pathlib import Path
from zipfile import ZipFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.forms.models import model_to_dict
from globals.c_globals import viewables, trainers, tf_workers
from camai.c_settings import safe_import
from camai.passwords import db_password
from camai.version import version
from tools.l_tools import djconf
from tools.l_break import break_type, BR_LONG
from startup.redis import my_redis as startup_redis
from streams.models import stream
from eventers.models import evt_condition
from users.models import userinfo
from access.c_access import access
from tf_workers.models import school, worker
from trainers.models import trainer, trainframe, trainframe_imex
from .models import camurl

#from .forms import UploadFileForm
#from pprint import pprint

emulatestatic = safe_import('emulatestatic')
db_database = safe_import('db_database')
no_nginx = safe_import('localaccess') or not safe_import('mydomain')

BASE_PATH = Path(settings.BASE_DIR)
DATAPATH = djconf.getconfigpath('datapath', default = 'data/', base = BASE_PATH)
SCHOOLSPATH = djconf.getconfigpath('schools_dir', default = 'schools/', base = DATAPATH)
VIRT_CAM_PATH = djconf.getconfigpath(
  'virt_cam_path', 
  default = 'virt_cam_path/', 
  base = DATAPATH,
) 
VIRT_CAM_PATH.mkdir(parents=True, exist_ok=True)
PARENTPATH = BASE_PATH.parent
(PARENTPATH / 'temp').mkdir(parents=True, exist_ok=True)
DOWN_BACKUP_PATH = PARENTPATH / 'temp' / 'backup'
shutil.rmtree(DOWN_BACKUP_PATH, ignore_errors=True)

class myTemplateView(LoginRequiredMixin, TemplateView):

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'emulatestatic' : emulatestatic,
      'is_public' : djconf.getconfigbool('is_public_server', False),
      'debug' : settings.DEBUG,
      'tf_debug' : self.request.user.is_superuser and djconf.getconfigbool(
        'do_tf_debug', 
        True,
      ),
      'camlist' : access.filter_items(
        stream.objects.filter(active=True).filter(cam_mode_flag__gt=0), 'C', 
        self.request.user, 'R'
      ),
      'detectorlist' : access.filter_items(
        stream.objects.filter(active=True).filter(det_mode_flag__gt=0), 'D', 
        self.request.user, 'R'
      ),
      'eventerlist' : access.filter_items(
        stream.objects.filter(active=True).filter(eve_mode_flag__gt=0), 'E', 
        self.request.user, 'R'
      ),
      'schoollist' : access.filter_items(
        school.objects.filter(active=True), 'S', 
        self.request.user, 'R'
      ),
      'schoollist_write' : access.filter_items(
        school.objects.filter(active=True), 'S', 
        self.request.user, 'W'
      ),
    })
    return context

  def get(self, request, *args, **kwargs):
    if self.request.user.is_superuser:
      return(super().get(request, *args, **kwargs))
    else:
      return(HttpResponse('No Access'))
      
class cam_inst_view(myTemplateView):   

  def get_context_data(self, **kwargs):
    streamlimit = userinfo.objects.get(user = self.request.user.id).allowed_streams
    streamcount = stream.objects.filter(creator = self.request.user.id, active = True, ).count()
    context = super().get_context_data(**kwargs)
    context.update({
      'streamlimit' : streamlimit,
      'streamcount' : streamcount,
      'mayadd' : (streamlimit > streamcount),
    })
    return context

class inst_cam_easy(cam_inst_view):
  template_name = 'tools/inst_cam_easy.html'

class inst_cam_expert(cam_inst_view):
  template_name = 'tools/inst_cam_expert.html' 

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'camurls' : camurl.objects.all(),
      'ipaddress' : kwargs['ip'],
      'ports' : json.loads(kwargs['ports']),
    })
    return context 
    
class inst_virt_cam(cam_inst_view):
  template_name = 'tools/inst_virt_cam.html'  
  
  def post(self, request):
    uploaded_file = request.FILES['file']
    fs = FileSystemStorage(location='temp/upload')
    filename = fs.save(uploaded_file.name, uploaded_file)
    file_path = fs.path(filename)
    cmds = ['ffprobe', '-v', 'fatal']
    cmds += ['-print_format', 'json', '-show_streams', file_path]
    p = subprocess.Popen(cmds, stdout = subprocess.PIPE)
    output, _ = p.communicate()
    probe = json.loads(output)
    #pprint(probe)
    if len(probe):
      duration = 0.0
      for item in probe['streams']:
        duration = max(duration, float(item['duration']))
      if duration < 1.0:
        print('Too short', duration)
        return redirect('/tools/virt_cam_error/too_short/'+str(round(duration * 1000))+'/')
      else:   
        print('OK', duration)
    else:
      print('This is not a Video File.')
      return redirect('/tools/virt_cam_error/no_video/0/')
    newstream = stream()
    newstream.save()
    filename = 'virt_cam_' + str(newstream.id) + '.' + filename.split('.')[-1]
    shutil.move(file_path, VIRT_CAM_PATH / filename)
    newstream.cam_url = filename
    newstream.eve_school = school.objects.filter(active=True).first()
    newstream.creator = request.user
    cap = cv.VideoCapture(VIRT_CAM_PATH / filename)
    newstream.cam_xres = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    newstream.cam_yres = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    newstream.cam_virtual_fps = cap.get(cv.CAP_PROP_FPS)
    newstream.name = 'Virtual Camera ' + str(round(newstream.cam_virtual_fps, 2)) + 'fps'
    newstream.save(update_fields=(
      'name',
      'cam_url', 
      'eve_school', 
      'creator', 
      'cam_xres', 
      'cam_yres', 
      'cam_virtual_fps', 
    ))
    if not request.user.is_superuser:
      myaccess = access_control()
      myaccess.vtype = 'X'
      myaccess.vid = newlineid
      myaccess.u_g_nr = request.user.id
      myaccess.r_w = 'W'
      myaccess.save()
      access.read_list_async()
    while startup_redis.get_start_stream_busy():
      break_type(BR_LONG)
    startup_redis.set_start_stream_busy(newstream.id)
    while (not (newstream.id in viewables and 'stream' in viewables[newstream.id])):
      break_type(BR_LONG)
    evt_condition.objects.filter(eventer = newstream).delete()
    new_condition = evt_condition(reaction = 1, eventer = newstream, y = 1)
    my_eventer = viewables[newstream.id]['E']
    my_eventer.inqueue.put(('new_condition', 1, model_to_dict(new_condition)))
    new_condition.save()
    return redirect('/')
    
class virt_cam_error(cam_inst_view):
  template_name = 'tools/virt_cam_error.html'  

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'text' : kwargs['text'],
      'length' : kwargs['length'] / 1000.0,
    })
    return context 

class scan_cam_expert(cam_inst_view):
  template_name = 'tools/scan_cam_expert.html'

class addschool(myTemplateView):
  template_name = 'tools/addschool.html'

  def get_context_data(self, **kwargs):
    schoollimit = userinfo.objects.get(user = self.request.user.id).allowed_schools
    schoolcount = school.objects.filter(creator = self.request.user.id, active = True, ).count()
    context = super().get_context_data(**kwargs)
    context.update({
      'schoollimit' : schoollimit,
      'schoolcount' : schoolcount,
      'mayadd'      : schoollimit > schoolcount,
      'is_linked'   : len(trainer.objects.get(id=1).wsname) > 0,
    })
    return context

class linkservers(myTemplateView):
  template_name = 'tools/linkservers.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'workerlist' : worker.objects.filter(active=True),
      'trainerlist' : trainer.objects.filter(active=True),
    })
    return context

class shutdown(myTemplateView):
  template_name = 'tools/shutdown.html'
      
class upgrade(myTemplateView):
  template_name = 'tools/upgrade.html'

  def get_context_data(self, **kwargs):
    url = 'https://api.github.com/repos/ludgerh/cam-ai/releases/latest'
    response = rget(url)
    if response.status_code == 200:
      response = json.loads(response.text)
    context = super().get_context_data(**kwargs)
    context.update({
      'new_version' : response['tag_name'][1:],
      'zip_url' : response['zipball_url']
    })
    return context
      
class backup(myTemplateView):
  template_name = 'tools/backup.html'
    
def downbackup(request, school_nr = None):
  if not request.user.is_superuser:
    return HttpResponse('No Access.', status=403)
  if school_nr:
    down_file_name = f'CAM-AI-school-{school_nr}.zip'
  else:  
    down_file_name = f'CAM-AI-backup-{version}.zip'
  if no_nginx:
    response = FileResponse(
      open(DOWN_BACKUP_PATH / down_file_name, 'rb'), 
      as_attachment = True, 
      filename = down_file_name,
    )
  else:     
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=' + down_file_name
    response['X-Accel-Redirect'] = '/protected/backup/' + down_file_name
  return(response)

      
class restore(myTemplateView):
  template_name = 'tools/restore.html'
    
  def dispatch(self, request, *args, **kwargs):
    if not request.user.is_superuser:
      return HttpResponse('No Access.', status=403)
    return super().dispatch(request, *args, **kwargs)
    
  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'phase' : 0,
    })
    return context

  def post(self, request, *args, **kwargs):
    global import_filename, import_filepath
    if 'myfile' not in request.FILES:
      return self.get(request, *args, **kwargs)
    myfile = request.FILES['myfile']
    upload_dir = Path(settings.BASE_DIR) / 'temp' / 'backup'
    upload_dir.mkdir(parents=True, exist_ok=True)
    fs = FileSystemStorage(location=str(upload_dir), base_url=None)
    import_filename = fs.save(myfile.name, myfile)
    import_filepath = fs.path(import_filename)
    context = self.get_context_data()
    context.update({
      'phase' : 1,
    })
    return self.render_to_response(context)
    
class process_restore(myTemplateView):  
  template_name = 'tools/process_restore.html'  
    
  def dispatch(self, request, *args, **kwargs):
    if not request.user.is_superuser:
      return HttpResponse('No Access.', status=403)
    return super().dispatch(request, *args, **kwargs)
    
  def post(self, request, *args, **kwargs):
    context = self.get_context_data()
    post_dict = request.POST.dict()
    print(post_dict)
    if post_dict['status'] != 'OK':
      context.update({
        'code' : 5,
        'message' : 'Remote server said: ' +  post_dict['status'],
      })
      return self.render_to_response(context)
    job_type = post_dict['job_type']
    if job_type == 'restore':
      check_files = 'check_files' in post_dict and post_dict['check_files'] == 'on'
      check_db = 'check_db' in post_dict and post_dict['check_db'] == 'on'
    elif job_type == 'import':
      check_models = 'check_models' in post_dict and post_dict['check_models'] == 'on'
      check_frames = 'check_frames' in post_dict and post_dict['check_frames'] == 'on'
    safe_name = Path(post_dict['file_name']).name
    zip_file = DOWN_BACKUP_PATH / safe_name
    if not zip_file.exists():
      context.update({
        'code' : 1,
        'message' : 'Zip-File missing...',
      })
      return self.render_to_response(context)
    unpack_dir = settings.BASE_DIR / 'temp' / 'unpack' / 'data'
    unpack_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_file) as zf:
      zf.extractall(unpack_dir)
    zip_file.unlink(missing_ok=True) 
    version_file = unpack_dir / 'upload.cfg' 
    try:
      file_meta = {}
      with version_file.open(encoding='utf-8', errors='ignore') as f:
        for line in f:
          line = line.strip()
          if not line or line.startswith('#'):
            continue
          if '=' in line:
            key, value = line.split('=', 1)
            file_meta[key.strip()] = value.strip()
    except FileNotFoundError:   
      context.update({
        'code' : 2,
        'message' : 'Version-File missing...',
      })
      return self.render_to_response(context)
    if 'version' not in file_meta:   
      context.update({
        'code' : 3,
        'message' : 'Version-File not correct...',
      })
      return self.render_to_response(context)
    if file_meta['version'] != version:   
      context.update({
        'code' : 4,
        'message' : 'Version mismatch: (' + file_meta['version'] + ' <> ' + version +')'
      })
      return self.render_to_response(context)
    if job_type == 'restore':
      for item in viewables.values():
        async_to_sync(item['stream'].stop)()
      if check_db:
        cmd = ['mariadb', '--user=CAM-AI', '--host=localhost', db_database]
        env = dict(os.environ, MYSQL_PWD = db_password)
        with open(unpack_dir / 'db.sql', 'rb') as f:
            subprocess.run(cmd, check=True, stdin=f, env=env)
      if check_files:
        path_to_exchange = DATAPATH
        shutil.move(DATAPATH, settings.BASE_DIR / 'temp/home/cam_ai/data.old')
        shutil.move(unpack_dir, DATAPATH)
        shutil.rmtree(settings.BASE_DIR / 'temp/home/cam_ai/data.old')
    elif job_type == 'import':
      while True:
        try:
          school_line = school.objects.get(name = 'temp123school456name789magic')
          break
        except school.DoesNotExist: 
          break_type(BR_LONG)
      school_line.name = file_meta['schoolname']
      #print(file_meta)
      school_line.delegation_level = int(file_meta['delegation_level'])
      this_school_path = SCHOOLSPATH / f'model{school_line.id}'
      school_line.dir = str(this_school_path) + '/'
      school_line.save(update_fields=('name', 'dir', 'delegation_level', ))
      this_school_path.mkdir(parents=True, exist_ok=True)
      model_path = this_school_path / 'model'
      frames_path = this_school_path / 'frames'
      if check_models:  
        if (unpack_dir / 'model').exists():
          shutil.move(unpack_dir / 'model', this_school_path / 'model')
      if check_frames:
        if (unpack_dir / 'frames').exists():
          shutil.move(unpack_dir / 'frames', this_school_path / 'frames')
          
        data_file = unpack_dir / 'db.dat'
        load = f"load data local infile '{data_file}' "
        load += "into table trainers_trainframe "
        load += "character set utf8mb4 "
        load += "fields terminated by '\t' escaped by '\\' "
        load += "lines terminated by '\n' "
        load += "("
        for item in trainframe_imex[:-1]:
          load += item + ','
        load += trainframe_imex[-1] + ');'
        
        data_file = unpack_dir / "db.dat"
        cols = ",".join(trainframe_imex)  # z.B. made,encrypted,...
        load = rf"""load data local infile '{data_file}'
          into table trainers_trainframe
          character set utf8mb4
          fields terminated by '\t' escaped by '\\'
          lines terminated by '\n'
          ({cols});
        """
        cmd = [
          'mariadb',
          '--user=CAM-AI',
          '--host=localhost',
          '--database', db_database,  
          '--local-infile=1',
          '--default-character-set=utf8mb4',
          '-e',
          load,
        ]
        env = dict(os.environ, MYSQL_PWD = db_password)
        subprocess.run(
          cmd, 
          check=True, 
          env=env, 
          stdout=subprocess.DEVNULL, 
          stderr=subprocess.DEVNULL,
        )
        trainframe.objects.filter(school=0).update(school=school_line.id)
    zip_file.unlink(missing_ok=True)  
    if job_type == 'restore':
      (path_to_exchange / 'db.sql').unlink(missing_ok=True) 
      (path_to_exchange / 'db.dat').unlink(missing_ok=True)  
      (path_to_exchange / 'upload.cfg').unlink(missing_ok=True)  
      startup_redis.set_shutdown_command(20)
      context.update({
        'code' : 0,
        'message' : 'OK, please wait one minute for restart...',
      })
    elif job_type == 'import':  
      context.update({
        'code' : 10,
        'message' : 'Done importing school. You can continue...',
      })
    return self.render_to_response(context)
  
def logout_and_redirect(request):
  logout(request)
  return redirect('/')

class sendlogs(LoginRequiredMixin, TemplateView):
  template_name = 'tools/sendlogs.html'

  def get_context_data(self, **kwargs):
    context = super().get_context_data(**kwargs)
    context.update({
      'emulatestatic' : emulatestatic,
      'version' : djconf.getconfig('version', 'X.Y.Z'),
      'smtp_server' : djconf.getconfig('smtp_server', forcedb=False),
      'smtp_account' : djconf.getconfig('smtp_account', forcedb=False),
    })
    return context

