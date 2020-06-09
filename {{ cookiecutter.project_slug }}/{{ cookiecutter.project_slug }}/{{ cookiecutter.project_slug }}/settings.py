from {{ cookiecutter.project_slug }}.envs.common import *
from {{ cookiecutter.project_slug }}.envs.local.db import *

SECRET_KEY = 'w)w@lz#)but(87fg)_#w_iwcfl1y&0g#i1f0j!cx9d5%lk#@rj'
DEBUG = True
ALLOWED_HOSTS = []

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s|%(levelname)s|%(process)d|%(thread)d|'
                      '%(filename)s:%(lineno)d|%(module)s.%(funcName)s|'
                      '%(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'main': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
