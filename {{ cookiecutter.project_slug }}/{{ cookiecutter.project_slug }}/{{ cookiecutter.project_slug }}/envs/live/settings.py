from {{ cookiecutter.project_slug }}.envs.common import *
from {{ cookiecutter.project_slug }}.envs.live.db import *

# TODO: you should re-generate it
SECRET_KEY = 'w)w@lz#)but(87fg)_#w_iwcfl1y&0g#i1f0j!cx9d5%lk#@rj'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s|%(levelname)s|%(process)d:%(thread)d|'
                      '%(filename)s:%(lineno)d|%(module)s.%(funcName)s|'
                      '%(message)s',
        },
    },
    'handlers': {
        'main_file': {
            'level': 'DEBUG',
            'class': 'common.loggers.DailyFileHandler',
            'filename': '/var/log/{{ cookiecutter.organization }}/{{ cookiecutter.project_slug }}/main.log',
            'formatter': 'standard',
        },
    },
    'loggers': {
        '': {
            'handlers': ['main_file'],
            'level': 'INFO',
        },
        'main': {
            'handlers': ['main_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['main_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['main_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# TODO: provide your sentry key here.
import sentry_sdk
from sentry_sdk.integrations.django import ignore_logger

sentry_sdk.init("Your sentry key")

ignore_logger('django.security.DisallowedHost')
