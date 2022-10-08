from django.db import models

class access_control(models.Model):
  vtype = models.CharField(max_length=1) # 'C', 'D', 'E', 'S' or '0'
  vid = models.IntegerField()
  u_g = models.CharField(max_length=1, default='U') # 'U' = user, 'G' = group
  u_g_nr = models.IntegerField(default=0) # 0 = all users/groups
  r_w  = models.CharField(max_length=1, default='R') # 'R' = read, 'W' = write, '0' = read and write

  def __str__(self):
    return(self.vtype+'_'+str(self.vid)+' '+self.u_g+'_'+str(self.u_g_nr)+' '+self.r_w)

