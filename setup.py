#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Do not import non-standard modules here, as it will mess up the installation in clients.
import re

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

# Read version number etc from other file
# http://stackoverflow.com/questions/2058802/how-can-i-get-the-version-defined-in-setup-py-setuptools-in-my-package
with open('tacos2.py') as mainfile:
    main_py = mainfile.read()
metadata = dict( re.findall(r"__([a-z]+)__ *= *'([^']+)'", main_py) )

setup(
    name='tacos2',
    version      = metadata['version'],
    license      = metadata['license'],
    author       = metadata['author'],
    author_email = metadata['email'],
    url          = metadata['url'],
    description="Easy-to-use TacosII implementation for Python",
    long_description=readme + '\n\n' + history,
    install_requires = ['pyserial'],
    py_modules = ['tacos2', 'dummy_serial'],
    keywords='tacos2 serial',
    classifiers=[
        'Development Status :: 1 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Manufacturing',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7', 
        'Programming Language :: Python :: 3', 
        'Programming Language :: Python :: 3.2', 
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Communications',
        'Topic :: Home Automation',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Hardware :: Hardware Drivers',
        'Topic :: Terminals :: Serial',
    ],
    test_suite='tests'
)
