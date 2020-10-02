from __future__ import print_function

from setuptools import setup
from setuptools.command.test import test as TestCommand

import os
import sys

import objectdict

ROOT = os.path.abspath(os.path.dirname(__file__))


def read(*filenames):
    buf = []
    for filename in filenames:
        filepath = os.path.join(ROOT, filename)
        try:
            with open(filepath, 'r') as f:
                buf.append(f.read())
        except IOError:
            # ignore tox IOError (no such file or directory)
            pass
    return '\n\n'.join(buf)


long_description = read('README.md')


setup(
    name='objectdict',
    version=objectdict.__version__,
    url='https://github.com/311labs/ObjectDict/',
    author='Ian Starnes',
    author_email='ian@311labs.com',
    tests_require=tests_require,
    cmdclass={'test': PyTest},
    description=(
        'A Python dict that supports attribute-style access as '
        'well as hierarchical keys, JSON serialization, ZIP compression, and more.'
    ),
    long_description=long_description,
    packages=['uberdict'],
    platforms='any',
    test_suite='tests',
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, <4',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    extras_require={
        'dev': ['check-manifest', 'wheel'],
    }
)