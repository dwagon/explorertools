#!/usr/bin/env python
# 
# Setup script for explorer tools
#

import os
from distutils.core import setup

setup_scripts=[os.path.join('bin', f) for f in os.listdir('bin')]
setup_classifiers=[
    'Intended Audience :: Systems Administrators',
    'License :: OSI Approved :: GNU General Public Licence (GPL)',
    'Operating System :: POSIX',
    'Topic :: System :: Systems Administration',
    ]

setup(
    name='explorertools',
    version='1.1',
    description='Explorer hardware analysis tools suite',
    author='Dougal Scott',
    url='https://github.com/dwagon/explorertools',
    author_email='dougal.scott@gmail.com',
    scripts=setup_scripts,
    packages=['explorer'],
    classifiers=setup_classifiers,
    )

#EOF
