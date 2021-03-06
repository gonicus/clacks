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
    name = "libinst.cfg.puppet.client",
    version = "1.0",
    author = "Cajus Pollmeier",
    author_email = "pollmeier@gonicus.de",
    description = "Repository and installation abstraction library",
    long_description = """
This library handles the installation, configuration and repositories
for various systems in your setup.
""",
    license = "LGPL",
    url = "http://www.gosa-project.org",
    classifiers = [
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

    download_url = "http://oss.gonicus.de/pub/gosa",
    packages = find_packages('src', exclude=['examples', 'tests']),
    namespace_packages = ['libinst.cfg.puppet'],
    package_dir={'': 'src'},

    include_package_data = True,
    package_data = {
    },

    #test_suite = "nose.collector",
    zip_safe = False,

    #setup_requires = ['nose==0.11.1', 'NoseXUnit', 'pylint'],
    install_requires = [
        'clacks.client',
        'clacks.dbus',
        'pyinotify',
        'GitPython',
        'PyYAML',
    ],


    entry_points = """
        [client.module]
        puppet = libinst.cfg.puppet.client.main:PuppetClient

        [dbus.module]
        puppet = libinst.cfg.puppet.client.dbus_main:PuppetDBusHandler
    """
)
