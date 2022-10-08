from multiprocessing import Process
from time import sleep
from l_buffer import l_buffer
from os import getpid

print()
print('PID'+str(getpid())+':', 'Starting Main Process (CAM-AI Viewer mode)')

class myclass1():
  def __init__(self):
    self.myqueue = l_buffer(envi='D', bcat=1, call=callback)

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
# Called from the processes that will get the callbacks 
process1.myqueue.register_callback()
process1.run()
sleep(timebase * 4)
process1.myqueue.stop()
sleep(timebase)

print()
print('PID'+str(getpid())+':', 'Starting Main Process (CAM-AI frame pipemode)')

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
    self.myqueue = l_buffer(envi='D', bcat=2)

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
