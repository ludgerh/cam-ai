# tools/l_cuda.py
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

import ctypes
from glob import glob
from importlib.util import find_spec

# TensorFlow finds the pip NVIDIA libraries through the RUNPATH of
# libtensorflow_framework.so.2. In TF 2.21 nvidia/cusolver/lib is missing there,
# so without LD_LIBRARY_PATH TensorFlow skips all GPUs
# ('Cannot dlopen some GPU libraries'). A library loaded before
# TensorFlow is found by its soname.
PRELOAD_LIBS = ('cusolver/lib/libcusolver.so.*', )

def preload_cuda_libs():
  """
  Load the CUDA libraries TensorFlow does not find by itself.
  Call before importing TensorFlow. Returns the list of loaded files.
  """
  spec = find_spec('nvidia')
  if spec is None or not spec.submodule_search_locations:
    return([])
  result = []
  for nvidia_dir in spec.submodule_search_locations:
    for pattern in PRELOAD_LIBS:
      for lib in sorted(glob(nvidia_dir + '/' + pattern)):
        try:
          ctypes.CDLL(lib, mode = ctypes.RTLD_GLOBAL)
          result.append(lib)
        except OSError:
          pass
  return(result)
