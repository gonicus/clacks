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


setup(
    name = "clacks.agent",
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
        'clacks.agent': ['data/agent.conf', 'data/*xsl', 'data/events/*', 'data/objects/*'],
        'clacks.agent.plugins.goto': ['data/events/*'],
    },

    test_suite = "nose.collector",
    zip_safe = False,

    setup_requires = [
        #'nose==0.11.1',
        #'NoseXUnit',
        'pylint',
        ],
    install_requires = [
        'clacks.common',
        'webob',
        'paste',
        'netaddr',
        'smbpasswd',
        'python_daemon',
        'lockfile',
        'dumbnet',
        'pycrypto',
        'unidecode',
        'sqlalchemy',
        'lepl',
        'setproctitle',
        ],
    dependency_links = [
        'http://oss.gonicus.de/pub/gosa/eggs',
        ],

    # Not installable this way:
    # dumbnet

    entry_points = """
        [console_scripts]
        clacks-agent = clacks.agent.main:main

        [agent.module]
        command = clacks.agent.command:CommandRegistry
        amqp_service = clacks.agent.amqp_service:AMQPService
        httpd = clacks.agent.httpd:HTTPService
        scheduler = clacks.agent.scheduler:SchedulerService
        acl = clacks.agent.acl:ACLResolver
        objects = clacks.agent.objects.index:ObjectIndex
        xmldb = clacks.agent.xmldb.handler:XMLDBHandler
        jsonrpc_service = clacks.agent.jsonrpc_service:JSONRPCService
        jsonrpc_om = clacks.agent.jsonrpc_objects:JSONRPCObjectMapper
        transliterate = clacks.agent.plugins.misc.transliterate:Transliterate
        gravatar = clacks.agent.plugins.misc.gravatar:Gravatar
        goto.network = clacks.agent.plugins.goto.network:NetworkUtils
        goto.client_service = clacks.agent.plugins.goto.client_service:ClientService
        inventory = clacks.agent.plugins.inventory.consumer:InventoryConsumer

        [object.type]
        string = clacks.agent.objects.types.base:StringAttribute
        integer = clacks.agent.objects.types.base:IntegerAttribute
        boolean = clacks.agent.objects.types.base:BooleanAttribute
        binary = clacks.agent.objects.types.base:BinaryAttribute
        unicodestring = clacks.agent.objects.types.base:UnicodeStringAttribute
        date = clacks.agent.objects.types.base:DateAttribute
        timestamp = clacks.agent.objects.types.base:TimestampAttribute
        sambalogonhours = clacks.agent.plugins.samba.logonhours:SambaLogonHoursAttribute

        [object.backend]
        ldap = clacks.agent.objects.backend.back_ldap:LDAP
        null = clacks.agent.objects.backend.back_null:NULL

        [object.comparator]
        like = clacks.agent.objects.comparator.strings:Like
        regex = clacks.agent.objects.comparator.strings:RegEx
        stringlength = clacks.agent.objects.comparator.strings:stringLength
        equals = clacks.agent.objects.comparator.basic:Equals
        greater = clacks.agent.objects.comparator.basic:Greater
        smaller = clacks.agent.objects.comparator.basic:Smaller
        isvalidsambadomainname = clacks.agent.plugins.samba.domain:IsValidSambaDomainName
        isvalidhostname = clacks.agent.plugins.misc.filter_validators:IsValidHostName
        isexistingdn = clacks.agent.plugins.misc.filter_validators:IsExistingDN
        isexistingdnoftype = clacks.agent.plugins.misc.filter_validators:IsExistingDnOfType

        [object.filter]
        concatstring = clacks.agent.objects.filter.strings:ConcatString
        replace = clacks.agent.objects.filter.strings:Replace
        stringToTime = clacks.agent.objects.filter.strings:StringToTime
        stringToDate = clacks.agent.objects.filter.strings:StringToDate
        dateToString = clacks.agent.objects.filter.strings:DateToString
        timeToString = clacks.agent.objects.filter.strings:TimeToString
        sambahash = clacks.agent.plugins.samba.hash:SambaHash
        target = clacks.agent.objects.filter.basic:Target
        setbackends = clacks.agent.objects.filter.basic:SetBackends
        setvalue = clacks.agent.objects.filter.basic:SetValue
        clear = clacks.agent.objects.filter.basic:Clear
        integertodatetime = clacks.agent.objects.filter.basic:IntegerToDatetime
        datetimetointeger = clacks.agent.objects.filter.basic:DatetimeToInteger
        sambaacctflagsin = clacks.agent.plugins.samba.flags:SambaAcctFlagsIn
        sambaacctflagsout = clacks.agent.plugins.samba.flags:SambaAcctFlagsOut
        sambamungedialin = clacks.agent.plugins.samba.munged:SambaMungedDialIn
        sambamungedialout = clacks.agent.plugins.samba.munged:SambaMungedDialOut
        generatesambasid = clacks.agent.plugins.samba.sid:GenerateSambaSid
        posixgetnextid = clacks.agent.plugins.posix.id:GetNextID
        datetoshadowdays = clacks.agent.plugins.posix.shadow:DateToShadowDays
        shadowdaystodate = clacks.agent.plugins.posix.shadow:ShadowDaysToDate
        password_methods = clacks.agent.plugins.password.methods:DetectPasswordMethod
        password_lock = clacks.agent.plugins.password.locking:DetectAccountLockStatus
        password_hash = clacks.agent.plugins.password.hash:GeneratePasswordHash
        addbackend = clacks.agent.objects.filter.basic:AddBackend

        [object.operator]
        and = clacks.agent.objects.operator.bool:And
        or = clacks.agent.objects.operator.bool:Or
        not = clacks.agent.objects.operator.bool:Not

        [xmldb.driver]
        berkleydb = clacks.agent.xmldb.driver.dbxml_driver:DBXml

        [object]
        object = clacks.agent.objects.proxy:ObjectProxy
    """,
)
