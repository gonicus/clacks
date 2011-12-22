#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name = "fts",
    version = "0.1",
    author = "Jan Wenzel",
    author_email = "wenzel@gonicus.de",
    description = "PXE/TFTP supplicant application",
    long_description = """
    This application generates pxelinux configuration files for systems identified by mac addresses.
    It needs a TFTP-Server to allow controlling network boot.
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
    namespace_packages = ['fts'],
    package_dir={'': 'src'},

    include_package_data = True,
    package_data = {
    },

    test_suite = "nose.collector",
    zip_safe = False,

    setup_requires = ['nose', 'NoseXUnit', 'pylint'],
    install_requires = [
        'clacks.agent',
        'fuse-python',
    ],

    entry_points = """
    [fts.methods]
    fai = fts.fai.main:FAI
""",
)
