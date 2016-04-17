#!/usr/bin/env python

import os
from setuptools import find_packages, setup
from jia import __version__

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

try:
    from setuptools import setup, find_packages
except ImportError:
    print("setuptools is required to build. Install it using"
            " your package manager (usually python-setuptools) or via pip (pip"
            " install setuptools).")
    sys.exit(1)

setup(
    name='jia',
    version=__version__,
    description='A simple provisioner for development projects',
    author='Matt Parrett',
    author_email='matt.parrett@gmail.com',
    url='http://github.com/mparrett/jia/',
    license='BSD License',
    install_requires=['paramiko', 'jinja2', 'PyYAML', 'setuptools', 'pycrypto >= 2.6', 'scp >= 0.8', 'docopt >= 0.6'],
    packages=['jia'],
    classifiers=[
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Information Technology',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: BSD License',
          'Natural Language :: English',
          'Operating System :: POSIX',
          'Programming Language :: Python :: 2.7',
          'Topic :: System :: Installation/Setup',
          'Topic :: System :: Systems Administration',
          'Topic :: Utilities',
    ],
    scripts=['bin/jia'],
    include_package_data=True
)
