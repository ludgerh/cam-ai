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

"""
Django settings for camai project.

Generated by 'django-admin startproject' using Django 4.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
from pathlib import Path
from .passwords import (db_password, security_key, localaccess, mydomain, myip, 
  smtp_account, smtp_password, smtp_server, smtp_port, smtp_email, smtp_use_ssl)
try:  
  from .passwords import httpsport
except  ImportError:
  httpsport = '' 
from .version import version

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = security_key

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []
if localaccess:
  ALLOWED_HOSTS =  ['127.0.0.1', 'localhost']
if myip:
  ALLOWED_HOSTS.append(myip)
if mydomain:
  ALLOWED_HOSTS.append(mydomain.split(':')[0])
  trustedorigin = 'https://'+mydomain
  if httpsport:
    trustedorigin += (':'+httpsport)
  CSRF_TRUSTED_ORIGINS = [trustedorigin]

# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django_tables2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django_registration',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'CAM-AI',
        'HOST': 'localhost',
        'PORT': '3306',
        'USER': 'CAM-AI',
        'PASSWORD': db_password,
    		'CONN_MAX_AGE': 3600,
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'https://static.cam-ai.de/'+version+'/'
#STATIC_URL = 'static/'
#STATICFILES_DIRS = [str(BASE_DIR)+'/camai/static', ]
STATIC_ROOT = str(BASE_DIR)+'/data/static'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
ACCOUNT_ACTIVATION_DAYS = 7 # One-week activation window
DEFAULT_FROM_EMAIL = smtp_email
EMAIL_HOST = smtp_server
EMAIL_HOST_PASSWORD = smtp_password
EMAIL_HOST_USER = smtp_account
EMAIL_PORT = smtp_port
EMAIL_USE_TLS = smtp_use_ssl
