#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = "fts",
    version = "1.0",
    author = "Jan Wenzel",
    author_email = "wenzel@gonicus.de",
    description = "PXE/TFTP supplicant application",
    long_description = """
    This application generates pxelinux configuration files for systems
    identified by MAC addresses.
    It needs a TFTP-Server to allow controlling network boot.""",
    license = "LGPL",
    url = "http://www.gosa-project.org",
    classifiers = [
        'Development Status :: 5 - Production/Stable',
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
    namespace_packages = ['fts'],
    package_dir={'': 'src'},

    include_package_data = True,
    package_data = { 'fts': ['data/config', 'data/pxelinux.static/default'] },

    test_suite = "nose.collector",
    zip_safe = False,

    install_requires = [
        'fuse-python',
    ],

    entry_points = """
        [console_scripts]
        fts = fts.main:main
    """
)
