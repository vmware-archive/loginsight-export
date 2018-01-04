#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


# VMware vRealize Log Insight Exporter
# Copyright © 2017 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an “AS IS” BASIS, without warranties or
# conditions of any kind, EITHER EXPRESS OR IMPLIED. See the License for the
# specific language governing permissions and limitations under the License.


try:
    version_namespace = {}
    with open('loginsightexport/__version__.py') as f:
        exec(f.read(), version_namespace)
    packageversion = version_namespace['version']
except (OSError, IOError, KeyError):
    packageversion = "0.dev0"


requires = ['requests', 'humanize']

setup(
    name="loginsight-export",
    version=packageversion,
    url='http://github.com/vmware/loginsight-export/',
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
        'Programming Language :: Python :: 3 :: Only',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: System :: Logging',
    ],
    entry_points={
        'console_scripts': [
            'loginsight-export = loginsightexport.__main__:main',
            'loginsight-export-convert-json = loginsightexport.convert:main'
        ]
    }
)
