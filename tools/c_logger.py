from logging import getLogger, DEBUG, FileHandler as LogFileHandler, StreamHandler as LogStreamHandler, Formatter
from tools.l_tools import djconf, logdict
from os import path, makedirs

def log_ini(logger, logname):
  logger.setLevel(DEBUG)
  pathwarning = None
  logpath = djconf.getconfig('logdir', default='data/logs/')
  if not path.exists(logpath):
    makedirs(logpath)
  levelwarning = None
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
  if pathwarning:
    logger.warning('Wrong path string from settimngs: '+pathwarning)
  if levelwarning:
    logger.warning('Wrong level string from settimngs: '+levelwarning)
