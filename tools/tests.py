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

from django.test import TestCase
from .l_tools import djconfig

class djconfigtest(TestCase):

  def test_schreiben_lesen_strings(self):
    """
    We write a db line with strings and read it
    """
    djconf = djconfig()
    djconf.setconfig('DontUseThisOneInRealLife', 'DoesNotMatter1')
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife') == 'DoesNotMatter1', True)
    djconf.setconfig('DontUseThisOneInRealLife', 'DoesNotMatter2')
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife') == 'DoesNotMatter2', True)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfig('DontUseThisOneInRealLife', 'DoesNotMatter3')  == 'DoesNotMatter3', True)

  def test_schreiben_lesen_int(self):
    """
    We write a db line with integers and read it
    """
    djconf = djconfig()
    djconf.setconfigint('DontUseThisOneInRealLife', 123456)
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife') == 123456, True)
    djconf.setconfigint('DontUseThisOneInRealLife', 234567)
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife') == 234567, True)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfigint('DontUseThisOneInRealLife', 345678)  == 345678, True)

  def test_schreiben_lesen_float(self):
    """
    We write a db line with floats and read it
    """
    djconf = djconfig()
    djconf.setconfigfloat('DontUseThisOneInRealLife', 123.456)
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife') == 123.456, True)
    djconf.setconfigfloat('DontUseThisOneInRealLife', 2.34567)
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife') == 2.34567, True)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfigfloat('DontUseThisOneInRealLife', 34567.8)  == 34567.8, True)

  def test_schreiben_lesen_bool(self):
    """
    We write a db line with floats and read it
    """
    djconf = djconfig()
    djconf.setconfigbool('DontUseThisOneInRealLife', True)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), True)
    djconf.setconfigbool('DontUseThisOneInRealLife', False)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), False)
    djconf.delconfig('DontUseThisOneInRealLife')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife') is None, True)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife', True), True)
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife', False), False)
    djconf.setconfig('DontUseThisOneInRealLife', '1')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), True)
    djconf.setconfig('DontUseThisOneInRealLife', '0')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), False)
    djconf.setconfig('DontUseThisOneInRealLife', 'Ja')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), True)
    djconf.setconfig('DontUseThisOneInRealLife', 'Nein')
    self.assertIs(djconf.getconfigbool('DontUseThisOneInRealLife'), False)

# load_plugin() with and without a compiled extension next to the source.
# The compiled case needs Cython and a C compiler and skips without them.

import sys
import shutil
import sysconfig
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import skipIf
from django.test import SimpleTestCase
from .l_tools import load_plugin

try:
  from Cython.Build import cythonize
  from setuptools import Extension
  from setuptools.dist import Distribution
  cython_missing = shutil.which(sysconfig.get_config_var('CC').split()[0]) is None
except ImportError:
  cython_missing = True

PLUGIN_SOURCE = 'import cython\nvalue = 42\ncompiled = cython.compiled\n'

class LoadPluginTest(SimpleTestCase):

  def setUp(self):
    tmpdir = TemporaryDirectory()
    self.addCleanup(tmpdir.cleanup)
    self.plugin_dir = Path(tmpdir.name) / 'plugins' / 'test_load_plugin'
    self.plugin_dir.mkdir(parents = True)
    self.plugin_file = self.plugin_dir / 'plugin.py'
    self.plugin_file.write_text(PLUGIN_SOURCE)
    self.module_name = 'plugins.test_load_plugin.plugin'
    self.addCleanup(sys.modules.pop, self.module_name, None)

  def test_loads_source(self):
    module = load_plugin(self.plugin_file)
    self.assertEqual(module.value, 42)
    self.assertFalse(module.compiled)
    self.assertEqual(module.__name__, self.module_name)
    self.assertIs(sys.modules[self.module_name], module)

  def test_returns_cached_module(self):
    module = load_plugin(self.plugin_file)
    self.assertIs(load_plugin(self.plugin_file), module)

  def test_base_package_missing(self):
    with self.assertRaises(ValueError):
      load_plugin(self.plugin_file, base_package = 'not_there')

  @skipIf(cython_missing, 'Cython or C compiler not available')
  def test_prefers_compiled(self):
    dist = Distribution({'ext_modules' : cythonize(
      [Extension(self.module_name, [str(self.plugin_file)])],
      compiler_directives = {'language_level' : 3},
      quiet = True,
    )})
    cmd = dist.get_command_obj('build_ext')
    cmd.build_temp = str(self.plugin_dir / 'build')
    cmd.build_lib = str(self.plugin_dir / 'lib')
    cmd.ensure_finalized()
    cmd.run()
    built = Path(cmd.get_ext_fullpath(self.module_name))
    shutil.copy(built, self.plugin_dir / built.name)
    module = load_plugin(self.plugin_file)
    self.assertEqual(module.value, 42)
    self.assertTrue(module.compiled)
    self.assertTrue(module.__file__.endswith(built.name))
