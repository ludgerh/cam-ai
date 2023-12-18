import json
from channels.generic.websocket import WebsocketConsumer
from .models import alarm as dbalarm

class alarm(WebsocketConsumer):

  def connect(self):
    if self.scope['user'].is_superuser:
      self.accept()

  def receive(self, text_data):
    params = json.loads(text_data)['data']	
    outlist = {'tracker' : json.loads(text_data)['tracker']}	
    print(text_data)

    if params['command'] == 'write_db':
      alarmline = dbalarm(name='test', mendef='text',action_type=1,action_param1='t',action_param2='t')
      alarmline.save()
      outlist['data'] = 'OK'
      print('--> ' + str(outlist))
      self.send(json.dumps(outlist))
