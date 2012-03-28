#!/usr/bin/env python
from setuptools import setup, find_packages
import os

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()


setup(
    name = "clacks.dbus",
    version = "1.0",
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
    packages = find_packages('src', exclude=['examples', 'tests']),
    package_dir = {'': 'src'},
    namespace_packages = ['clacks'],

    include_package_data = True,
    package_data = {
        'clacks.dbus.plugins.inventory': ['data/fusionToClacks.xsl'],
    },

    test_suite = "nose.collector",

    setup_requires = [
        'python_dateutil',
        ],
    install_requires = [
        'clacks.common',
        'setproctitle'
        ],
    dependency_links = [
        'http://oss.gonicus.de/pub/gosa/eggs',
        ],

    entry_points = """
        [console_scripts]
        clacks-dbus = clacks.dbus.main:main
        notify-user = clacks.dbus.notify:main

        [dbus.module]
        unix = clacks.dbus.plugins.services.main:DBusUnixServiceHandler
        inventory = clacks.dbus.plugins.inventory.main:DBusInventoryHandler
        service = clacks.dbus.plugins.services.main:DBusUnixServiceHandler
        notify = clacks.dbus.plugins.notify.main:DBusNotifyHandler
        wol = clacks.dbus.plugins.wakeonlan.main:DBusWakeOnLanHandler
        shell = clacks.dbus.plugins.shell.main:DBusShellHandler
    """,
)
