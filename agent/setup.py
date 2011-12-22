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
        ],
    dependency_links = [
        'http://oss.gonicus.de/pub/gosa/eggs',
        ],

    # Not installable this way:
    # dumbnet

    entry_points = """
        [console_scripts]
        clacks-agent = clacks.agent.main:main

        [gosa.modules]
        module.command = clacks.agent.command:CommandRegistry
        module.amqp_service = clacks.agent.amqp_service:AMQPService
        module.httpd = clacks.agent.httpd:HTTPService
        module.scheduler = clacks.agent.scheduler:SchedulerService
        module.acl = clacks.agent.acl:ACLResolver
        module.objects = clacks.agent.objects.index:ObjectIndex
        module.xmldb = clacks.agent.xmldb.handler:XMLDBHandler
        module.jsonrpc_service = clacks.agent.jsonrpc_service:JSONRPCService
        module.jsonrpc_om = clacks.agent.jsonrpc_objects:JSONRPCObjectMapper
        module.samba.utils = clacks.agent.plugins.samba.utils:SambaUtils
        module.misc.utils = clacks.agent.plugins.misc.utils:MiscUtils
        module.gravatar.utils = clacks.agent.plugins.gravatar.utils:GravatarUtils
        module.goto.network = clacks.agent.plugins.goto.network:NetworkUtils
        module.goto.client_service = clacks.agent.plugins.goto.client_service:ClientService
        module.inventory = clacks.agent.plugins.inventory.consumer:InventoryConsumer

        [gosa.object.type]
        type.string = clacks.agent.objects.types.base:StringAttribute
        type.integer = clacks.agent.objects.types.base:IntegerAttribute
        type.boolean = clacks.agent.objects.types.base:BooleanAttribute
        type.binary = clacks.agent.objects.types.base:BinaryAttribute
        type.unicodestring = clacks.agent.objects.types.base:UnicodeStringAttribute
        type.date = clacks.agent.objects.types.base:DateAttribute
        type.timestamp = clacks.agent.objects.types.base:TimestampAttribute
        type.sambalogonhours = clacks.agent.plugins.samba.utils:SambaLogonHoursAttribute

        [gosa.object.backend]
        backend.ldap = clacks.agent.objects.backend.back_ldap:LDAP
        backend.null = clacks.agent.objects.backend.back_null:NULL

        [gosa.object.comparator]
        comparator.like = clacks.agent.objects.comparator.strings:Like
        comparator.regex = clacks.agent.objects.comparator.strings:RegEx
        comparator.stringlength = clacks.agent.objects.comparator.strings:stringLength
        comparator.equals = clacks.agent.objects.comparator.basic:Equals
        comparator.greater = clacks.agent.objects.comparator.basic:Greater
        comparator.smaller = clacks.agent.objects.comparator.basic:Smaller
        filter.isvalidsambadomainname = clacks.agent.plugins.samba.utils:IsValidSambaDomainName

        [gosa.object.filter]
        filter.concatstring = clacks.agent.objects.filter.strings:ConcatString
        filter.replace = clacks.agent.objects.filter.strings:Replace
        filter.stringToTime = clacks.agent.objects.filter.strings:StringToTime
        filter.stringToDate = clacks.agent.objects.filter.strings:StringToDate
        filter.dateToString = clacks.agent.objects.filter.strings:DateToString
        filter.timeToString = clacks.agent.objects.filter.strings:TimeToString
        filter.sambahash = clacks.agent.plugins.samba.utils:SambaHash
        filter.target = clacks.agent.objects.filter.basic:Target
        filter.setbackends = clacks.agent.objects.filter.basic:SetBackends
        filter.setvalue = clacks.agent.objects.filter.basic:SetValue
        filter.clear = clacks.agent.objects.filter.basic:Clear
        filter.integertodatetime = clacks.agent.objects.filter.basic:IntegerToDatetime
        filter.datetimetointeger = clacks.agent.objects.filter.basic:DatetimeToInteger
        filter.sambaacctflagsin = clacks.agent.plugins.samba.utils:SambaAcctFlagsIn
        filter.sambaacctflagsout = clacks.agent.plugins.samba.utils:SambaAcctFlagsOut
        filter.sambamungedialin = clacks.agent.plugins.samba.utils:SambaMungedDialIn
        filter.sambamungedialout = clacks.agent.plugins.samba.utils:SambaMungedDialOut
        filter.generatesambasid = clacks.agent.plugins.samba.utils:GenerateSambaSid
        filter.posixgetnextid = clacks.agent.plugins.posix.utils:GetNextID
        filter.datetoshadowdays = clacks.agent.plugins.posix.utils:DateToShadowDays
        filter.shadowdaystodate = clacks.agent.plugins.posix.utils:ShadowDaysToDate
        filter.detectpasswordmethod = clacks.agent.plugins.password.utils:DetectPasswordMethod
        filter.detectaccountlockstatus = clacks.agent.plugins.password.utils:DetectAccountLockStatus
        filter.generatepasswordhash = clacks.agent.plugins.password.utils:GeneratePasswordHash
        filter.addbackend = clacks.agent.objects.filter.basic:AddBackend

        [gosa.object.operator]
        operator.and = clacks.agent.objects.operator.bool:And
        operator.or = clacks.agent.objects.operator.bool:Or
        operator.not = clacks.agent.objects.operator.bool:Not

        [xmldb]
        berkley.driver = clacks.agent.xmldb.driver.dbxml_driver:DBXml
    """,
)
