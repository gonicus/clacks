#!/usr/bin/env python
# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

from setuptools import setup, find_packages

setup(
    name="libinst.boot.preseed",
    version="1.0",
    author="Jan Wenzel",
    author_email="wenzel@gonicus.de",
    description="Repository and installation abstraction library",
    long_description="""
This library handles the installation, configuration and repositories
for various systems in your setup.
""",
    license="GPL",
    url="http://www.gosa-project.org",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Monitoring',
    ],

    download_url="http://oss.gonicus.de/pub/gosa",
    namespace_packages=['libinst'],
    packages=find_packages('src', exclude=['examples', 'tests']),
    package_dir={'': 'src'},

    include_package_data=False,

    test_suite="nose.collector",
    zip_safe=False,

    setup_requires=['pylint'],
    install_requires=[
        'libinst',
    ],


    entry_points="""
        [libinst.base_methods]
        libinst.preseed = libinst.boot.preseed.methods:DebianPreseed

        [object]
        libinst.preseed.diskdefinition = libinst.boot.preseed.disk:DebianDiskDefinition
    """
)
