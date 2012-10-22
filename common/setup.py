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

import os
import platform
from setuptools import setup, find_packages

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()


common_install_requires = [
    'zope.interface>=3.5',
    'babel',
    'pyOpenSSL',
    'lxml',
    'qpid-python',
    ],

if platform.system() == "Windows":
    common_install_requires[0].append([
        'pybonjour',
    ])

else:
    # Not installable this way:
    # avahi, pygtk (gobject), dbus
    #install_requires[0].append([
    #    'dbus',
    #    'avahi',
    #    'PyGTK',
    #])
    pass


setup(
    name = "clacks.common",
    version = "0.8",
    author = "Cajus Pollmeier",
    author_email = "pollmeier@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
    long_description = README + "\n\n" + CHANGES,
    keywords = "system config management ldap groupware",
    license = "LGPL",
    url = "http://www.gosa-project.org",
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Monitoring',
    ],

    download_url = "http://oss.gonicus.de/pub/gosa",
    packages = find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages = ['clacks'],

    include_package_data = True,
    package_data = {
        'clacks.common': ['data/stylesheets/*', 'data/events/*'],
    },

    test_suite = "nose.collector",
    zip_safe = False,

    setup_requires = [
        #'nose==0.11.1',
        #'coverage',
        #'NoseXUnit',
        'pylint',
        'babel',
        ],
    install_requires = common_install_requires,
    dependency_links = [
        'http://oss.gonicus.de/pub/gosa/eggs',
        ],

    entry_points = """
        [agent.module]
        amqp = clacks.common.components.amqp:AMQPHandler
        error = clacks.common.error:ClacksErrorHandler

        [json.datahandler]
        datetime = clacks.common.components.jsonrpc_utils:DateTimeHandler
        date = clacks.common.components.jsonrpc_utils:DateTimeDateHandler
        factory = clacks.common.components.jsonrpc_utils:FactoryHandler
        blob = clacks.common.components.jsonrpc_utils:BinaryHandler
    """,
)
