# Copyright (C) 2023 Ludger Hellerhoff, ludger@cam-ai.de
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

from logging import getLogger, DEBUG, FileHandler as LogFileHandler, StreamHandler as LogStreamHandler, Formatter
from tools.l_tools import djconf, logdict
from os import path, makedirs

def log_ini(logger, logname):
  logger.setLevel(DEBUG)
  datapath = djconf.getconfig('datapath', 'data/')
  logpath = djconf.getconfig('logdir', default = datapath + 'logs/')
  if not path.exists(logpath):
    makedirs(logpath)
  loglevelstring = djconf.getconfig('loglevel', default='INFO')
  fh = LogFileHandler(logpath+logname+'.log')
  fh.setLevel(logdict[loglevelstring])
  ch = LogStreamHandler()
  ch.setLevel(logdict[loglevelstring])
  formatter = Formatter("{asctime} [{levelname:8}] {message}",
    "%d.%m.%Y %H:%M:%S","{")
  ch.setFormatter(formatter)
  fh.setFormatter(formatter)
  logger.addHandler(ch)
  logger.addHandler(fh)
  logger.info('Started Process '+logname+'...')
