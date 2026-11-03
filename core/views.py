# core/views.py
"""
Copyright (C) 2026 by the CAM-AI team, info@cam-ai.de
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

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from tools.l_tools import load_plugin
from .models import plugin

@login_required
def plugin_view(request, plugin_id):
  # Hands the request to the view defined in a view plugin
  dbline = get_object_or_404(plugin, id = plugin_id, type = 'V')
  plugin_mod = load_plugin(dbline.path)
  return(plugin_mod.plugin(dbline.path).view(request))
