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

from multiprocessing import Process
from time import sleep
from l_buffer import l_buffer
from os import getpid

print()
print('PID'+str(getpid())+':', 'CAM-AI Viewer mode')

class myclass1():
  def __init__(self):
    self.myqueue = l_buffer(envi='D', call=callback)

  def run(self):
    self.run_process = Process(target=self.runner)
    self.run_process.start()

  def runner(self):
    print('PID'+str(getpid())+':', 'Starting Runner 1')
    self.myqueue.put('Sample 1')
    sleep(timebase)
    self.myqueue.put('Sample 2')
    sleep(timebase)
    self.myqueue.put('Sample 3')

def callback():
  print('PID'+str(getpid())+':', 'Callback1:', process1.myqueue.get())
 
timebase = 0.1
process1 = myclass1()
process1.myqueue.register_callback()
process1.run()
sleep(timebase * 4)
process1.myqueue.stop()
sleep(timebase)

print()
print('PID'+str(getpid())+':', 'CAM-AI frame pipemode, no Put-Locking')

class myclass2(): #myclass2 represents the sending process

  def run(self):
    self.run_process = Process(target=self.runner)
    self.run_process.start()

  def runner(self):
    print('PID'+str(getpid())+':', 'Starting Runner 2')
    sleep(timebase/2)
    print('PID'+str(getpid())+':', 'Putting Sample 1')
    self.parent.myqueue.put('Sample 1')
    sleep(timebase)
    print('PID'+str(getpid())+':', 'Putting Sample 2')
    self.parent.myqueue.put('Sample 2')
    sleep(timebase)
    print('PID'+str(getpid())+':', 'Putting Sample 3')
    self.parent.myqueue.put('Sample 3')
    sleep(timebase)

class myclass3(): #myclass3 represents the receiving process
  def __init__(self):
    self.myqueue = l_buffer(envi='D', bget=True)

  def run(self):
    self.run_process = Process(target=self.runner)
    self.run_process.start()

  def runner(self):
    print('PID'+str(getpid())+':', 'Starting Runner 3')
    print('PID'+str(getpid())+':', 'Getting:', self.myqueue.get())
    print('PID'+str(getpid())+':', 'Getting:', self.myqueue.get())
    print('PID'+str(getpid())+':', 'Getting:', self.myqueue.get())
    self.myqueue.stop()
 
timebase = 0.1
process3 = myclass3()
process2 = myclass2()
process2.parent = process3
process2.run()
process3.run()
sleep(4 * timebase)
sleep(timebase)

print()
print('PID'+str(getpid())+':', 'CAM-AI frame pipemode, with Put-Locking')

class myclass4(): #myclass2 represents the sending process

  def run(self):
    self.run_process = Process(target=self.runner)
    self.run_process.start()

  def runner(self):
    print('PID'+str(getpid())+':', 'Starting Runner 4')
    self.parent.myqueue.put('Sample 1')
    print('PID'+str(getpid())+':', 'Put Sample 1')
    self.parent.myqueue.put('Sample 2')
    print('PID'+str(getpid())+':', 'Put Sample 2')
    self.parent.myqueue.put('Sample 3')
    print('PID'+str(getpid())+':', 'Put Sample 3')
    sleep(timebase)
    self.parent.myqueue.stop()

class myclass5(): #myclass3 represents the receiving process
  def __init__(self):
    self.myqueue = l_buffer(envi='D', bput=True)

  def run(self):
    self.run_process = Process(target=self.runner)
    self.run_process.start()

  def runner(self):
    print('PID'+str(getpid())+':', 'Starting Runner 5')
    sleep(timebase/2)
    print('PID'+str(getpid())+':', 'Getting:', self.myqueue.get())
    sleep(timebase)
    print('PID'+str(getpid())+':', 'Getting:', self.myqueue.get())
    sleep(timebase)
    print('PID'+str(getpid())+':', 'Getting:', self.myqueue.get())
    sleep(timebase)
 
timebase = 0.1
process5 = myclass5()
process4 = myclass4()
process4.parent = process5
process4.run()
process5.run()
sleep(4 * timebase)
