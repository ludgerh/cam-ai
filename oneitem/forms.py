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

from django import forms
from streams.models import stream

class CamForm(forms.ModelForm):

	class Meta:
		model = stream
		fields = (
      'name',
      'cam_pause', 
      'cam_fpslimit', 
      'cam_feed_type', 
      'cam_url', 
    )
		widgets = { 
      'cam_pause' : forms.CheckboxInput(),
			'cam_fpslimit' : forms.NumberInput(attrs={'size': 10, 'min' : 0, 'max' : 100, 'step' : 0.1}), 
			'cam_url' : forms.TextInput(attrs={'size': 70}),
		}

class DetectorForm(forms.ModelForm):

	class Meta:
		model = stream
		fields = (
      'det_fpslimit', 
      'det_threshold', 
      'det_backgr_delay', 
      'det_dilation', 
      'det_erosion', 
      'det_max_size', 
      'det_max_rect',
    )
		widgets = {
			'det_fpslimit' : forms.NumberInput(attrs={'size': 10, 'min' : 0, 'max' : 100, 'step' : 0.1}), 
			'det_threshold' : forms.NumberInput(attrs={'size': 10, 'min' : 1, 'max' : 254}), 
			'det_backgr_delay' : forms.NumberInput(attrs={'size': 10, 'min' : 0, 'max' : 100}), 
			'det_dilation' : forms.NumberInput(attrs={'size': 10, 'min' : 1, 'max' : 200}), 
			'det_erosion' : forms.NumberInput(attrs={'size': 10, 'min' : 0, 'max' : 100}), 
			'det_max_size' : forms.NumberInput(attrs={'size': 10, 'min' : 1, 'max' : 200}), 
			'det_max_rect' : forms.NumberInput(attrs={'size': 10, 'min' : 1, 'max' : 100}), 
		}

class EventerForm(forms.ModelForm):

	class Meta:
		model = stream
		fields = (
      'eve_fpslimit',
      'eve_margin', 
      'eve_event_time_gap', 
      'eve_school', 
      'eve_alarm_email',
    )
		widgets = {
			'eve_fpslimit' : forms.NumberInput(attrs={'size': 10, 'min' : 0, 'max' : 100, 'step' : 0.1}), 
			'eve_margin' : forms.NumberInput(attrs={'size': 10, 'min' : 0, 'max' : 100}), 
			'eve_event_time_gap' : forms.NumberInput(attrs={'size': 10, 'min' : 1, 'max' : 3600}), 
			#'eve_school' : forms.NumberInput(attrs={'size': 10, 'min' : 1, 'max' : 100}), 
			'eve_alarm_email' : forms.TextInput(attrs={'size': 70}),
		}
