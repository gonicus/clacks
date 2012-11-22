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
import os
import platform

try:
    from babel.messages import frontend as babel
except:
    pass

setup(
    name = "clacks.phone",
    version = "0.1",
    author = "Dennis Radon",
    author_email = "radon@gonicus.de",
    description = "Event handling for Asterisk based setups",
    long_description = "TBD",
    keywords = "amqp telephony notification",
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

    packages = find_packages('src', exclude=['examples', 'tests']),
    package_dir={'': 'src'},
    namespace_packages = ['clacks'],

    include_package_data = True,
    package_data = {
        'clacks.phone': ['data/events/*xsd', 'data/phone.png', 'locale/*/*/*.mo'],
    },

    install_requires = [
        'clacks.agent',
        'PIL',
        ],

    entry_points = """
        [agent.module]
        ami-resolver = clacks.phone.main:PhoneNotificationReceiver

        [phone.resolver]
        res.clacks = clacks.phone.modules.clacks_res:ClacksNumberResolver
        res.sugar = clacks.phone.modules.sugar_res:SugarNumberResolver
        res.xml = clacks.phone.modules.xml_res:XMLNumberResolver

        [notification.renderer]
        render.main = clacks.phone.modules.common_render:CommonRenderer
        render.goforge = clacks.phone.modules.goforge_render:GOForgeRenderer
        render.tb = clacks.phone.modules.doingreport_render:DoingReportRenderer

    """,
    #res.telekom = clacks.phone.modules.telekom_res:TelekomNumberResolver
    #res.ldap = clacks.phone.modules.ldap_res:LDAPNumberResolver
)
