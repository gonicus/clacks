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
    name = "gosa.dbus",
    version = "3.0",
    author = "Cajus Pollmeier",
    author_email = "pollmeier@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
    long_description = README + "\n\n" + CHANGES,
    keywords = "system config management ldap groupware",
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
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: System :: Software Distribution',
        'Topic :: System :: Monitoring',
    ],

    download_url = "http://oss.gonicus.de/pub/gosa",
    packages = find_packages('src', exclude=['examples', 'tests']),
    package_dir = {'': 'src'},
    namespace_packages = ['gosa'],

    include_package_data = True,
    package_data = {
        'gosa.dbus.plugins.inventory': ['data/fusionToGosa.xsl'],
    },

    test_suite = "nose.collector",

    setup_requires = [
        'nose==0.11.1',
        'NoseXUnit',
        'pylint',
        'babel',
        'python_dateutil',
        ],
    install_requires = [
        'gosa.common',
        ],
    dependency_links = [
        'http://oss.gonicus.de/pub/gosa/eggs',
        ],

    entry_points = """
        [console_scripts]
        clacks-dbus = gosa.dbus.main:main
        notify-user = gosa.dbus.notify:main

        [gosa_dbus.modules]
        module.unix = gosa.dbus.plugins.services.main:DBusUnixServiceHandler
        module.inventory = gosa.dbus.plugins.inventory.main:DBusInventoryHandler
        module.service = gosa.dbus.plugins.services.main:DBusUnixServiceHandler
        module.notify = gosa.dbus.plugins.notify.main:DBusNotifyHandler
        module.wol = gosa.dbus.plugins.wakeonlan.main:DBusWakeOnLanHandler
    """,
)
