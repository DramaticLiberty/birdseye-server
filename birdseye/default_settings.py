import os
DEBUG = (os.getenv('DEBUG', 0) == 1)
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_DATABASE_URI = str(os.getenv(
    'SQLALCHEMY_DATABASE_URI',
    'postgresql://birdseye:birdseye@localhost/birdseye'))
RQ_SCHEDULER_INTERVAL = 60
RQ_ASYNC = DEBUG == 1

LOGGER = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'filters': [],
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
        },
        'sqlalchemy.engine': {
            'handlers': ['default'],
            'level': 'WARN',
            'propagate': False
        },
        'sqlalchemy.pool': {
            'handlers': ['default'],
            'level': 'WARN',
            'propagate': False
        },
        'sqlalchemy.dialects.postgresql': {
            'handlers': ['default'],
            'level': 'WARN',
            'propagate': False
        },
    }
}
