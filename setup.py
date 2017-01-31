#!/usr/bin/env python

import sys
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

try:
    version_namespace = {}
    with open('loginsightexport/__version__.py') as f:
        exec(f.read(), version_namespace)
    packageversion = version_namespace['version']
except (OSError, IOError, KeyError):
    packageversion = "0.dev0"


requires = ['requests', 'humanize']

setup(
    name="loginsightexport",
    version=packageversion,
    url='http://github.com/vmware/pyloginsight/export/',
    license='Apache Software License 2.0',
    author='Alan Castonguay',
    install_requires=requires,
    tests_require=requires + ["requests_mock", "pytest", "pytest-catchlog", "pytest-flakes", "pytest-pep8", "tox"],
    description='Log Insight Export',
    author_email='acastonguay@vmware.com',
    long_description=open('README.md').read(),
    packages=find_packages(),
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 1 - Planning',
        'Natural Language :: English',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    entry_points={
        'console_scripts': [
            'loginsightexport = loginsightexport.__main__:main'
        ]
    }
)
