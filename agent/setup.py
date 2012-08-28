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
        'tornado',
        'python-Levenshtein',
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
        search = clacks.agent.objects.index:SearchWrapper
        xmldb = clacks.agent.xmldb.handler:XMLDBHandler
        jsonrpc_service = clacks.agent.jsonrpc_service:JSONRPCService
        jsonrpc_om = clacks.agent.jsonrpc_objects:JSONRPCObjectMapper
        transliterate = clacks.agent.plugins.misc.transliterate:Transliterate
        locales = clacks.agent.plugins.misc.locales:Locales
        shells = clacks.agent.plugins.posix.shells:ShellSupport
        guimethods = clacks.agent.plugins.gui.methods:GuiMethods
        gravatar = clacks.agent.plugins.misc.gravatar:Gravatar
        goto.network = clacks.agent.plugins.goto.network:NetworkUtils
        goto.client_service = clacks.agent.plugins.goto.client_service:ClientService
        inventory = clacks.agent.plugins.inventory.consumer:InventoryConsumer
        password = clacks.agent.plugins.password.manager:PasswordManager
        gofon = clacks.agent.plugins.gofon.gofon:goFonAccount
        gosa = clacks.agent.plugins.gosa.service:GOsaService

        [object.type]
        string = clacks.agent.objects.types.base:StringAttribute
        anytype = clacks.agent.objects.types.base:AnyType
        integer = clacks.agent.objects.types.base:IntegerAttribute
        boolean = clacks.agent.objects.types.base:BooleanAttribute
        binary = clacks.agent.objects.types.base:BinaryAttribute
        unicodestring = clacks.agent.objects.types.base:UnicodeStringAttribute
        date = clacks.agent.objects.types.base:DateAttribute
        timestamp = clacks.agent.objects.types.base:TimestampAttribute
        sambalogonhours = clacks.agent.plugins.samba.logonhours:SambaLogonHoursAttribute
        devicepartitiontabletype = clacks.agent.plugins.goto.goto_types:DevicePartitionTableType
        aclrole = clacks.agent.objects.types.acl_roles:AclRole
        aclset = clacks.agent.objects.types.acl_set:AclSet

        [object.backend]
        ldap = clacks.agent.objects.backend.back_ldap:LDAP
        Object_handler = clacks.agent.objects.backend.back_object_handler:ObjectHandler
        null = clacks.agent.objects.backend.back_null:NULL
        json = clacks.agent.objects.backend.back_json:JSON
        sql = clacks.agent.objects.backend.back_sql:SQL
        dbmap = clacks.agent.objects.backend.back_db_map:DBMAP

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
        objectwithpropertyexists = clacks.agent.plugins.misc.filter_validators:ObjectWithPropertyExists
        isexistingdnoftype = clacks.agent.plugins.misc.filter_validators:IsExistingDnOfType
        is_acl_role = clacks.agent.objects.comparator.acl_roles:IsAclRole
        is_acl_set = clacks.agent.objects.comparator.acl_set:IsAclSet

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
        stringtodatetime = clacks.agent.objects.filter.basic:StringToDatetime
        datetimetostring = clacks.agent.objects.filter.basic:DatetimeToString
        sambaacctflagsin = clacks.agent.plugins.samba.flags:SambaAcctFlagsIn
        sambaacctflagsout = clacks.agent.plugins.samba.flags:SambaAcctFlagsOut
        sambamungedialin = clacks.agent.plugins.samba.munged:SambaMungedDialIn
        sambamungedialout = clacks.agent.plugins.samba.munged:SambaMungedDialOut
        generatesambasid = clacks.agent.plugins.samba.sid:GenerateSambaSid
        posixgetnextid = clacks.agent.plugins.posix.filters:GetNextID
        generategecos = clacks.agent.plugins.posix.filters:GenerateGecos
        loadgecosstate = clacks.agent.plugins.posix.filters:LoadGecosState
        generateids = clacks.agent.plugins.posix.filters:GenerateIDs
        datetoshadowdays = clacks.agent.plugins.posix.shadow:DatetimeToShadowDays
        shadowdaystodate = clacks.agent.plugins.posix.shadow:ShadowDaysToDatetime
        detect_pwd_method = clacks.agent.plugins.password.filter.detect_method:DetectPasswordMethod
        password_lock = clacks.agent.plugins.password.filter.detect_locking:DetectAccountLockStatus
        addbackend = clacks.agent.objects.filter.basic:AddBackend
        registereddevicestatusin = clacks.agent.plugins.goto.in_out_filters:registeredDeviceStatusIn
        registereddevicestatusout = clacks.agent.plugins.goto.in_out_filters:registeredDeviceStatusOut

        [object.operator]
        and = clacks.agent.objects.operator.bool:And
        or = clacks.agent.objects.operator.bool:Or
        not = clacks.agent.objects.operator.bool:Not

        [xmldb.driver]
        berkleydb = clacks.agent.xmldb.driver.dbxml_driver:DBXml

        [object]
        object = clacks.agent.objects.proxy:ObjectProxy

        [password.methods]
        crypt_method = clacks.agent.plugins.password.crypt_password:PasswordMethodCrypt
    """,
)
