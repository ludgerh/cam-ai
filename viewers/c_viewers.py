from threading import Lock
from l_buffer.l_buffer import l_buffer
from drawpad.drawpad import drawpad

class c_viewer():

  def __init__(self, parent, logger):
    self.logger = logger
    self.parent = parent
    self.inqueue = l_buffer(envi='D', call=self.callback)
    self.onf_dict_lock = Lock()
    self.onf_dict = {}
    if self.parent.type in {'C', 'D'}:
      self.drawpad = drawpad(self, self.logger)

  def callback(self):   
    with self.onf_dict_lock:
      for item in self.onf_dict.values():
        item(self)

  def push_to_onf(self, onf):
    count = 0
    with self.onf_dict_lock:
      while count in self.onf_dict:
        count += 1
      self.onf_dict[count] = onf
    return(count)

  def pop_from_onf(self, count):
    with self.onf_dict_lock:
	    del self.onf_dict[count]

  def stop(self):
    self.inqueue.stop()

