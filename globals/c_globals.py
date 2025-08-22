"""
Copyright (C) 2025 by the CAM-AI team, info@cam-ai.de
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

trainers = {}
tf_workers = {}
viewables = {}
viewers = {}

def initialize():
  from sys import argv
  if not((argv[0].endswith('manage.py') and 'runserver' in argv) or (argv[0].endswith('gunicorn'))):
    return()
  import django
  django.setup()
  from multiprocessing import SimpleQueue, Lock as p_lock
  from tf_workers.models import worker as worker_mod
  from tf_workers.c_tf_workers import tf_worker
  for item in worker_mod.objects.filter(active=True):
    tf_workers[item.id] = tf_worker(item.id, )
    #Tricky: Queues and buffers stay in this Process, even if not named
  from trainers.models import trainer as trainer_mod
  from trainers.c_trainers import trainer
  glob_lock = p_lock()
  my_worker = tf_workers[1] #may variable in the future 
  for item in trainer_mod.objects.filter(active=True):
    trainers[item.id] = trainer(
      item.id, 
      my_worker.inqueue,
      my_worker.registerqueue,
      glob_lock,
    )
    #Tricky: Queues and buffers stay in this Process, even if not named
  from streams.models import stream as stream_mod
  from streams.c_streams import c_stream
  for item in stream_mod.objects.filter(active=True):
    add_stream(c_stream(item.id))
  from access.c_access import initialize as access_initialize
  access_initialize()
  from dyndns.views import initialize as dyndns_initialize
  dyndns_initialize()
  
def add_viewer(viewer):
  if viewer.id not in viewers:
    viewers[viewer.id] = {}
  viewers[viewer.id][viewer.type] = viewer
  
def add_stream(stream):
  if stream.id not in viewables:
    viewables[stream.id] = {}
  viewables[stream.id]['stream'] = stream 
    
def add_viewable(viewable):
  if viewable.id not in viewables:
    viewables[viewable.id] = {}
  viewables[viewable.id][viewable.type] = viewable  
