# -*- coding: utf-8 -*-
'''
Project Birdseye server source package
'''
from gevent import monkey
monkey.patch_all(thread=False)

from flask import Flask  # noqa
from flask_sqlalchemy import SQLAlchemy  # noqa
import logging.config  # noqa
import sys  # noqa


def _get_version():
    try:
        import birdseye.version  # pragma: no cover
        return birdseye.version.ver  # pragma: no cover
    except:
        import setuptools_scm
        return setuptools_scm.get_version(root='..', relative_to=__file__)

__version__ = _get_version()


def get_semver():
    scm_ver = __version__
    return scm_ver[:scm_ver.index('.dev')] if '.dev' in scm_ver else scm_ver

app = Flask(__name__)
app.config.from_object('birdseye.default_settings')

if 'LOGGER' in app.config:
    logging.config.dictConfig(app.config['LOGGER'])
else:
    handler = logging.StreamHandler(stream=sys.stdout)
    app.logger.addHandler(handler)
    app.logger.setLevel('INFO')

db = SQLAlchemy(app)

import birdseye.api  # noqa
birdseye.api.noqa()
