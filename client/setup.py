#!/usr/bin/env python
from setuptools import setup, find_packages
import os
import platform

try:
    from babel.messages import frontend as babel
except:
    pass

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README')).read()
CHANGES = open(os.path.join(here, 'CHANGES')).read()


client_install_requires = [
    'clacks.common',
    'netaddr',
    'netifaces',
    'python_dateutil',
    ],

if platform.system() == "Windows":
    import py2exe

    client_install_requires[0].append([
        'pybonjour',
    ])

    modules = ""
    joiner = """
        join.cli = clacks.client.plugins.join.cli:Cli
    """
else:
    client_install_requires[0].append([
        'python_daemon',
        'lockfile',
    ])

    modules = """
        inventory = clacks.client.plugins.inventory.utils:Inventory
        service = clacks.client.plugins.dbus.proxy:DBUSProxy
        powermanagement = clacks.client.plugins.powermanagement.utils:PowerManagement
        session = clacks.client.plugins.sessions.main:SessionKeeper
    """
    joiner = """
        join.qt = clacks.client.plugins.join.qt_gui:CuteGUI
        join.curses = clacks.client.plugins.join.curses_gui:CursesGUI
        join.cli = clacks.client.plugins.join.cli:Cli
    """

setup(
    name = "clacks.client",
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
    package_dir={'': 'src'},
    namespace_packages = ['clacks'],

    include_package_data = True,
    package_data = {
        'clacks.client': ['data/client.conf'],
        'clacks.client.plugins.inventory': ['data/xmlToChecksumXml.xsl'],
    },

    test_suite = "nose.collector",
    zip_safe = False,

    setup_requires = [
        #'nose==0.11.1',
        #'NoseXUnit',
        'pylint',
        'babel',
        ],
    install_requires = client_install_requires,
    dependency_links = [
        'http://oss.gonicus.de/pub/gosa/eggs',
        ],

    entry_points = """
        [console_scripts]
        clacks-client = clacks.client.main:main
        clacks-join = clacks.client.join:main

        [join.module]
        %(joiner)s

        [client.module]
        command = clacks.client.command:ClientCommandRegistry
        amqp = clacks.client.amqp:AMQPClientHandler
        amqp_service = clacks.client.amqp_service:AMQPClientService
        %(modules)s
    """ % {'modules': modules, 'joiner': joiner},

    console=['clacks/client/gcs.py']
)
