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
    name = "clacks.utils",
    version = "0.8",
    author = "GONICUS GmbH",
    author_email = "info@gonicus.de",
    description = "Identity-, system- and configmanagement middleware",
    keywords = "system config management ldap groupware",
    license = "GPL",
    url = "http://clacks-project.org",
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

    download_url = "http://oss.gonicus.de",
    packages = find_packages('src', exclude=['examples', 'tests']),
    package_dir = {'': 'src'},
    namespace_packages = ['clacks'],

    include_package_data = False,
    zip_safe = False,

    setup_requires = ['pylint', 'babel' ],
    install_requires = ['clacks.common'],

    entry_points = """
        [console_scripts]
        clacksh = clacks.shell.main:main
        acl-admin = clacks.utils.acl_admin:main
        clacks-ldap-monitor = clacks.utils.clacks_ldap_monitor:main
        clacks-plugin-skel = clacks.utils.clacks_plugin_skel:main
        schema2xml = clacks.utils.schema2xml:main
        update-i18n = clacks.utils.update_i18n:main
    """,
)
