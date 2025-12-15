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

import os
from .c_settings import safe_import
from pathlib import Path
from .version import version
  
debugpw = safe_import('debugpw') 
debug_daphne = safe_import('debug_daphne') 
debug_channels = safe_import('debug_channels') 
emulatestatic = safe_import('emulatestatic') 
data_path = safe_import('data_path') 
db_database = safe_import('db_database') 
db_password = safe_import('db_password') 
security_key = safe_import('security_key') 
localaccess = safe_import('localaccess') 
myip = safe_import('myip') 
mydomain = safe_import('mydomain') 
httpsport = safe_import('httpsport') 
mail_client_url = safe_import('mail_client_url') 
smtp_account = safe_import('smtp_account') 
smtp_password = safe_import('smtp_password') 
smtp_server = safe_import('smtp_server') 
smtp_port = safe_import('smtp_port') 
smtp_email = safe_import('smtp_email') 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = security_key

# SECURITY WARNING: don't run with debug turned on in production!
# Don't change the settings here, got to passwords.py instead
if emulatestatic:
  DEBUG = True
else:  
  DEBUG = debugpw

if localaccess:
  ALLOWED_HOSTS =  ['127.0.0.1', 'localhost']
  CLIENT_URL = 'http://localhost:8000/'
else:  
  ALLOWED_HOSTS = []
if myip:
  if isinstance(myip, str):
    ALLOWED_HOSTS += [myip]
    CLIENT_URL = 'http://' + myip + ':8000/'
  else:
    ALLOWED_HOSTS += myip
    CLIENT_URL = 'http://' + myip[0] + ':8000/'
if mydomain:
  ALLOWED_HOSTS.append(mydomain.split(':')[0])
  trustedorigin = 'https://'+mydomain
  if httpsport:
    trustedorigin += (':'+httpsport)
  CLIENT_URL = trustedorigin + '/'
  CSRF_TRUSTED_ORIGINS = [trustedorigin]
if mail_client_url:  
  CLIENT_URL = mail_client_url  

# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django_tables2',
    'django_htmx',
    'django.contrib.admin',
    'django.contrib.auth',
    'django_registration',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap4',
    'config',
    'accounts',
    'tools',
    'l_buffer',
    'viewers',
    'streams',
    'access',
    'index',
    'oneitem',
    'detectors',
    'eventers',
    'tf_workers',
    'drawpad',
    'trainers',
    'schools',
    'users',
    'ws_predictions',
    'onvif',
    'cleanup',
    'startup',
]

if debug_daphne or debug_channels:
  LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
      'console': {
        'level': 'ERROR', 
        'class': 'logging.StreamHandler',
      },
      # You can add more handlers if needed, such as file handlers
    },
    'loggers': {},
  }
  
if debug_daphne:
  LOGGING['loggers']['daphne'] =  {
    'handlers': ['console'],
    'level': 'ERROR',
    'propagate': False,
  }
  
if debug_channels:
  LOGGING['loggers']['channels'] =  {
    'handlers': ['console'],
    'level': 'ERROR',
    'propagate': False,
  }


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
]

ROOT_URLCONF = 'camai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR)+'/camai/templates/', ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'camai.wsgi.application'
ASGI_APPLICATION = 'camai.asgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'camai.db_backend',
        'NAME': db_database,
        'HOST': 'localhost',
        'PORT': '3306',
        'USER': 'CAM-AI',
        'PASSWORD': db_password,
        'CONN_MAX_AGE': 60,   # keep-alive connections for 60 seconds
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
  {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
  {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
  {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
  {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATICFILES_DIRS = [
  str(BASE_DIR)+'/camai/static', 
  str(BASE_DIR)+'/accounts/static', 
]

if emulatestatic:
  #Development config, needs debug
  STATIC_URL = 'static/'
else:  
  #Production config
  STATIC_URL = 'https://static.cam-ai.de/'+version+'/'
  STATIC_ROOT = str(BASE_DIR)+'/'+data_path+'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ACCOUNT_ACTIVATION_DAYS = 7 # One-week activation window
DEFAULT_FROM_EMAIL = smtp_email

CRISPY_TEMPLATE_PACK = 'bootstrap4'

EMAIL_HOST = smtp_server
EMAIL_HOST_PASSWORD = smtp_password
EMAIL_HOST_USER = smtp_account
EMAIL_PORT = smtp_port
EMAIL_FROM = smtp_email

