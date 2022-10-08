from django.db import models

class setting(models.Model):
	setting =  models.CharField(max_length=100)
	value =  models.CharField(max_length=100)
	comment =  models.CharField(max_length=255)

	def __str__(self):
		return('Setting: ' + self.setting+' = ' + self.value)
