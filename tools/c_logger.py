"""
Copyright (C) 2024-2025 by the CAM-AI team, info@cam-ai.de
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

import aiofiles
from logging import DEBUG, FileHandler as LogFileHandler, StreamHandler as LogStreamHandler, Formatter
from tools.l_tools import djconf, logdict
from os import path, makedirs

def do_log_ini(logger, logname, logpath, loglevelstring):
  logger.setLevel(DEBUG)
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
  logger.info('Started log for process '+logname+'...')

def log_ini(logger, logname):
  datapath = djconf.getconfig('datapath', 'data/')
  logpath = djconf.getconfig('logdir', default = datapath + 'logs/')
  makedirs(logpath, exist_ok=True)
  loglevelstring = djconf.getconfig('loglevel', default='INFO')
  do_log_ini(logger, logname, logpath, loglevelstring)

async def alog_ini(logger, logname):
  datapath = await djconf.agetconfig('datapath', 'data/')
  logpath = await djconf.agetconfig('logdir', default = datapath + 'logs/')
  if not await aiofiles.os.path.exists(logpath):
    await aiofiles.os.makedirs(logpath)
  loglevelstring = await djconf.agetconfig('loglevel', default='INFO')
  do_log_ini(logger, logname, logpath, loglevelstring)
