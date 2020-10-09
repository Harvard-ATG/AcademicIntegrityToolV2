"""
Django settings for academic_integrity_tool_v2 project.
Generated by 'django-admin startproject' using Django 1.10.5 of TLT template.
For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os
import logging
from .secure import SECURE_SETTINGS
from django.utils.log import DEFAULT_LOGGING

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# NOTE: Since we have a settings module, we have to go one more directory up to get to
# the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Toggle for the Django Debug Toolbar
DEBUG_TOOLBAR = False

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'policy_wizard',
    'lti_provider',
    'tinymce',
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

# Authentication

# Django defaults are below, but will need to be customized if using something
# other than the built-in Django auth, such as PIN, LTI, etc.
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'lti_provider.auth.LTIBackend',
)
# LOGIN_URL = '/accounts/login'

ROOT_URLCONF = 'academic_integrity_tool_v2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'academic_integrity_tool_v2.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': SECURE_SETTINGS.get('db_default_name', 'academic_integrity_tool_v2'),
        'USER': SECURE_SETTINGS.get('db_default_user', 'academic_integrity_tool_v2'),
        'PASSWORD': SECURE_SETTINGS.get('db_default_password'),
        'HOST': SECURE_SETTINGS.get('db_default_host', '127.0.0.1'),
        'PORT': SECURE_SETTINGS.get('db_default_port', 5432),  # Default postgres port
    },
}

# Sessions
# https://docs.djangoproject.com/en/1.9/topics/http/sessions/#module-django.contrib.sessions

# Store sessions in default cache defined below
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# NOTE: This setting only affects the session cookie, not the expiration of the session
# being stored in the cache.  The session keys will expire according to the value of
# SESSION_COOKIE_AGE (https://docs.djangoproject.com/en/1.9/ref/settings/#session-cookie-age),
# which defaults to 2 weeks.
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Cache
# https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-CACHES

REDIS_HOST = SECURE_SETTINGS.get('redis_host', '127.0.0.1')
REDIS_PORT = SECURE_SETTINGS.get('redis_port', 6379)

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': "redis://%s:%s/0" % (REDIS_HOST, REDIS_PORT),
        'OPTIONS': {
            'PARSER_CLASS': 'redis.connection.HiredisParser'
        },
        'KEY_PREFIX': 'academic_integrity_tool_v2',  # Provide a unique value for shared cache
        # See following for default timeout (5 minutes as of 1.7):
        # https://docs.djangoproject.com/en/1.9/ref/settings/#std:setting-CACHES-TIMEOUT
        'TIMEOUT': SECURE_SETTINGS.get('default_cache_timeout_secs', 300),
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'
# A boolean that specifies whether Django's translation system should be enabled. This provides
# an easy way to turn it off, for performance. If this is set to False, Django will make some
# optimizations so as not to load the translation machinery.
USE_I18N = False
# A boolean that specifies if localized formatting of data will be enabled by default or not.
# If this is set to True, e.g. Django will display numbers and dates using the format of the
# current locale.  NOTE: this would only really come into play if your locale was outside of the
# US
USE_L10N = False
# A boolean that specifies if datetimes will be timezone-aware by default or not. If this is set to
# True, Django will use timezone-aware datetimes internally. Otherwise, Django will use naive
# datetimes in local time.
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

# This directory is being ignored by git
STATIC_ROOT = os.path.normpath(os.path.join(BASE_DIR, 'http_static'))
STATIC_URL = '/static/'

# Logging
# https://docs.djangoproject.com/en/1.9/topics/logging/#configuring-logging

# Turn off default Django logging
# https://docs.djangoproject.com/en/1.9/topics/logging/#disabling-logging-configuration
LOGGING_CONFIG = None

_DEFAULT_LOG_LEVEL = SECURE_SETTINGS.get('log_level', logging.DEBUG)
_LOG_ROOT = SECURE_SETTINGS.get('log_root', '')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s\t%(asctime)s.%(msecs)03dZ\t%(name)s:%(lineno)s\t%(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S'
        },
        'simple': {
            'format': '%(levelname)s\t%(name)s:%(lineno)s\t%(message)s',
        },
        'django.server': DEFAULT_LOGGING['formatters']['django.server'],
    },
    'handlers': {
        # By default, log to a file
        'default': {
            'class': 'logging.handlers.WatchedFileHandler',
            'level': _DEFAULT_LOG_LEVEL,
            'formatter': 'verbose',
            'filename': os.path.join(_LOG_ROOT, 'django-academic_integrity_tool_v2.log'),
        },
        'django.server': DEFAULT_LOGGING['handlers']['django.server'],
    },
    # This is the default logger for any apps or libraries that use the logger
    # package, but are not represented in the `loggers` dict below.  A level
    # must be set and handlers defined.  Setting this logger is equivalent to
    # setting and empty string logger in the loggers dict below, but the separation
    # here is a bit more explicit.  See link for more details:
    # https://docs.python.org/2.7/library/logging.config.html#dictionary-schema-details
    'root': {
        'level': logging.WARNING,
        'handlers': ['default'],
    },
    'loggers': {
        # Add app specific loggers here, should look something like this:
        # '': {
        #    'level': _DEFAULT_LOG_LEVEL,
        #    'handlers': ['default'],
        #    'propagate': False,
        # },
        # Make sure that propagate is False so that the root logger doesn't get involved
        # after an app logger handles a log message.
        'django.server': DEFAULT_LOGGING['loggers']['django.server'],
    },
}

# Other project specific settings
LTI_TOOL_CONFIGURATION = {
    'title': 'Academic Integrity Policy',
    'description': 'An LTI-compliant tool that enables instructors and administrators to easily create, edit, and publish academic policies.',
    'launch_url': 'lti/launch/',
    'embed_url': '',
    'navigation': True,
}


PYLTI_CONFIG = {
    'consumers': {
        SECURE_SETTINGS['CONSUMER_KEY']: {
            'secret': SECURE_SETTINGS['LTI_SECRET']
        }
    }
}






X_FRAME_OPTIONS = SECURE_SETTINGS.get('X_FRAME_OPTIONS', 'ALLOW-FROM https://canvas.harvard.edu')
