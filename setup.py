# -*- coding: utf-8 -*
"""
Setup script for birdseye.

USAGE:
    python setup.py install
    python setup.py nosetests
"""

import sys
import os.path
HERE0 = os.path.dirname(__file__) or os.curdir
os.chdir(HERE0)
HERE = os.curdir
sys.path.insert(0, HERE)

from setuptools import find_packages, setup

# -----------------------------------------------------------------------------
# CONFIGURATION:
# -----------------------------------------------------------------------------
python_version = float("%s.%s" % sys.version_info[:2])
requirements = ['Baker',
                'decorator',
                'email_validator',
                'email-normalize',
                'Flask',
                'Flask-Uploads',
                'Jinja2',
                'gunicorn',
                'gevent',
                'psycopg2',
                'Pillow',
                'python-dateutil',
                'python-gcm',
                'pytz',
                'requests[security]',
                'schema',
                'termcolor',
                'tinify',
                'beautifulsoup4',
                'SQLAlchemy',
                'GeoAlchemy2',
                'Flask-SQLAlchemy',
                'Flask-Migrate',
                'Flask-RESTful',
                'Flask-Script',
                'google-cloud-vision',
                'piexif',
                'Flask-RQ2',
                'pubnub']

README = os.path.join(HERE, "README.rst")
description = "".join(open(README).readlines()[4:])
PROVIDES = ['birdseye']


# -----------------------------------------------------------------------------
# UTILITY:
# -----------------------------------------------------------------------------
def find_packages_by_root_package(packages):
    """
    Better than excluding everything that is not needed,
    collect only what is needed.
    """
    all_packages = []
    for p in packages:
        where = os.path.join(HERE, p)
        root_package = os.path.basename(where)
        all_packages.append(root_package)
        all_packages.extend(
            "%s.%s" % (root_package, sub_package)
            for sub_package in find_packages(where))
    return all_packages


# -----------------------------------------------------------------------------
# SETUP:
# -----------------------------------------------------------------------------
setup(
    name="birdseye",
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description="birdseye - the server for species migration observation.",
    long_description=description,
    author="Mihai Balint",
    author_email="balint.mihai@gmail.com",
    url="http://bitbucket.com/mibalint/birdseye",
    provides=PROVIDES,
    packages=find_packages_by_root_package(PROVIDES),
    include_package_data=True,
    py_modules=[],
    scripts=['bin/birdseye', 'bin/birdseye-test'],
    entry_points={
        "console_scripts": [],
        "distutils.commands": [],
    },
    install_requires=requirements,
    test_suite="nose.collector",
    tests_require=[
        "nose>=1.3", "mock>=1.0", "PyHamcrest>=1.8", "nose-timer>=0.7.0"],
    cmdclass={
    },
    extras_require={},
    use_2to3=False,
    license="BSD",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "License :: OSI Approved :: BSD License",
        "Intended Audience :: Developers",
        "Topic :: Office/Business",
    ],
    zip_safe=True,
)
