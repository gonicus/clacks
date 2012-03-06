# -*- coding: utf-8 -*- #
import dbxml
import random
import string
import time
import os
from random import choice

bases = """dc=xmpp,dc=gonicus,dc=de
ou=aclroles,dc=gonicus,dc=de
ou=Administrativa,dc=gonicus,dc=de
ou=apps,dc=gonicus,dc=de
ou=apps,ou=Consulting,dc=gonicus,dc=de
ou=apps,ou=GL,dc=gonicus,dc=de
ou=apps,ou=Technik,dc=gonicus,dc=de
ou=apps,ou=Vertrieb,dc=gonicus,dc=de
ou=asterisk,ou=configs,ou=systems,dc=gonicus,dc=de
ou=Auszubildende,dc=gonicus,dc=de
ou=CA,dc=gonicus,dc=de
ou=conferences,ou=asterisk,ou=configs,ou=systems,dc=gonicus,dc=de
ou=configs,ou=systems,dc=gonicus,dc=de
ou=configs,ou=systems,ou=Consulting,dc=gonicus,dc=de
ou=configs,ou=systems,ou=GL,dc=gonicus,dc=de
ou=configs,ou=systems,ou=Technik,dc=gonicus,dc=de
ou=configs,ou=systems,ou=Vertrieb,dc=gonicus,dc=de
ou=Consulting,dc=gonicus,dc=de
ou=customers,dc=gonicus,dc=de
ou=Datenschutz,dc=gonicus,dc=de
ou=devices,ou=systems,dc=gonicus,dc=de
ou=disk,ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=disk,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=disk,ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=Einkauf,dc=addressbook,dc=gonicus,dc=de
ou=Entwicklung,dc=gonicus,dc=de
ou=etch,ou=apps,dc=gonicus,dc=de
ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=Extern,dc=gonicus,dc=de
ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=FusionDirectory,ou=configs,ou=systems,dc=gonicus,dc=de
ou=GL,dc=gonicus,dc=de
ou=gofax,ou=systems,dc=gonicus,dc=de
ou=gofax,ou=systems,ou=Consulting,dc=gonicus,dc=de
ou=gofax,ou=systems,ou=GL,dc=gonicus,dc=de
ou=gofax,ou=systems,ou=Technik,dc=gonicus,dc=de
ou=gofax,ou=systems,ou=Vertrieb,dc=gonicus,dc=de
ou=gosa,ou=configs,ou=systems,dc=gonicus,dc=de
ou=groups,dc=gonicus,dc=de
ou=groups,ou=Administrativa,dc=gonicus,dc=de
ou=groups,ou=Auszubildende,dc=gonicus,dc=de
ou=groups,ou=Consulting,dc=gonicus,dc=de
ou=groups,ou=Datenschutz,dc=gonicus,dc=de
ou=groups,ou=Entwicklung,dc=gonicus,dc=de
ou=groups,ou=Extern,dc=gonicus,dc=de
ou=groups,ou=GL,dc=gonicus,dc=de
ou=groups,ou=samba,dc=gonicus,dc=de
ou=groups,ou=Technik,dc=gonicus,dc=de
ou=groups,ou=Testbed,dc=gonicus,dc=de
ou=groups,ou=Vertrieb,dc=gonicus,dc=de
ou=groups,ou=Webspace,ou=Extern,dc=gonicus,dc=de
ou=hooks,ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=hooks,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=hooks,ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=macros,ou=asterisk,ou=configs,ou=systems,dc=gonicus,dc=de
ou=packages,ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=packages,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=packages,ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=people,dc=gonicus,dc=de
ou=people,dc=webdav,dc=gonicus,dc=de
ou=people,ou=Administrativa,dc=gonicus,dc=de
ou=people,ou=Auszubildende,dc=gonicus,dc=de
ou=people,ou=Consulting,dc=gonicus,dc=de
ou=people,ou=Datenschutz,dc=gonicus,dc=de
ou=people,ou=Entwicklung,dc=gonicus,dc=de
ou=people,ou=Extern,dc=gonicus,dc=de
ou=people,ou=GL,dc=gonicus,dc=de
ou=people,ou=Phones,ou=Technik,dc=gonicus,dc=de
ou=people,ou=Technik,dc=gonicus,dc=de
ou=people,ou=Testbed,dc=gonicus,dc=de
ou=people,ou=Vertrieb,dc=gonicus,dc=de
ou=people,ou=Webspace,ou=Extern,dc=gonicus,dc=de
ou=phones,ou=systems,dc=gonicus,dc=de
ou=phones,ou=systems,ou=Auszubildende,dc=gonicus,dc=de
ou=phones,ou=systems,ou=Consulting,dc=gonicus,dc=de
ou=phones,ou=systems,ou=Entwicklung,dc=gonicus,dc=de
ou=phones,ou=systems,ou=Extern,dc=gonicus,dc=de
ou=phones,ou=systems,ou=GL,dc=gonicus,dc=de
ou=phones,ou=systems,ou=Phones,ou=Technik,dc=gonicus,dc=de
ou=phones,ou=systems,ou=Technik,dc=gonicus,dc=de
ou=phones,ou=systems,ou=Vertrieb,dc=gonicus,dc=de
ou=Phones,ou=Technik,dc=gonicus,dc=de
ou=policies,dc=gonicus,dc=de
ou=printers,ou=systems,dc=gonicus,dc=de
ou=printers,ou=systems,ou=Testbed,dc=gonicus,dc=de
ou=printers,ou=systems,ou=Vertrieb,dc=gonicus,dc=de
ou=profiles,ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=profiles,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=profiles,ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=Repository,ou=Extern,dc=gonicus,dc=de
ou=samba,dc=gonicus,dc=de
ou=sarge,ou=apps,dc=gonicus,dc=de
ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=scripts,ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=scripts,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=scripts,ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=servers,ou=systems,dc=gonicus,dc=de
ou=servers,ou=systems,ou=Consulting,dc=gonicus,dc=de
ou=servers,ou=systems,ou=GL,dc=gonicus,dc=de
ou=servers,ou=systems,ou=Technik,dc=gonicus,dc=de
ou=servers,ou=systems,ou=Vertrieb,dc=gonicus,dc=de
ou=sudoers,dc=gonicus,dc=de
ou=systems,dc=gonicus,dc=de
ou=systems,ou=Auszubildende,dc=gonicus,dc=de
ou=systems,ou=Consulting,dc=gonicus,dc=de
ou=systems,ou=Entwicklung,dc=gonicus,dc=de
ou=systems,ou=Extern,dc=gonicus,dc=de
ou=systems,ou=GL,dc=gonicus,dc=de
ou=systems,ou=Phones,ou=Technik,dc=gonicus,dc=de
ou=systems,ou=Technik,dc=gonicus,dc=de
ou=systems,ou=Testbed,dc=gonicus,dc=de
ou=systems,ou=Vertrieb,dc=gonicus,dc=de
ou=Technik,dc=addressbook,dc=gonicus,dc=de
ou=Technik,dc=gonicus,dc=de
ou=templates,ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=templates,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=templates,ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=terminals,ou=systems,dc=gonicus,dc=de
ou=terminals,ou=systems,ou=Consulting,dc=gonicus,dc=de
ou=terminals,ou=systems,ou=Entwicklung,dc=gonicus,dc=de
ou=terminals,ou=systems,ou=GL,dc=gonicus,dc=de
ou=terminals,ou=systems,ou=Technik,dc=gonicus,dc=de
ou=terminals,ou=systems,ou=Vertrieb,dc=gonicus,dc=de
ou=Testbed,dc=gonicus,dc=de
ou=variables,ou=etch,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=variables,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=variables,ou=sarge,ou=fai,ou=configs,ou=systems,dc=gonicus,dc=de
ou=Vertrieb,dc=addressbook,dc=gonicus,dc=de
ou=Vertrieb,dc=gonicus,dc=de
ou=Webspace,ou=Extern,dc=gonicus,dc=de
ou=winstations,ou=systems,dc=gonicus,dc=de
ou=winstations,ou=systems,ou=Technik,dc=gonicus,dc=de
ou=workstations,ou=systems,dc=gonicus,dc=de
ou=workstations,ou=systems,ou=GL,dc=gonicus,dc=de
ou=workstations,ou=systems,ou=Technik,dc=gonicus,dc=de""".split("\n")

entry1 = """
    <User>
        <UUID>096cf03c-ed95-102f-823b-812492b1b75c</UUID>
        <Type>User</Type>
        <DN>%(dn)s</DN>
        <ParentDN>%(base)s</ParentDN>
        <LastChanged>2011-06-29T09:08:25</LastChanged>
        <Extensions>
            <Extension>PosixUser</Extension>
            <Extension>SambaUser</Extension>
        </Extensions>
        <Attributes>
            <CtxCallback/>
            <CtxCallbackNumber/>
            <CtxCfgFlags1>00e00010</CtxCfgFlags1>
            <CtxCfgPresent>551e0bb0</CtxCfgPresent>
            <CtxInitialProgram/>
            <CtxKeyboardLayout/>
            <CtxMaxConnectionTime>0</CtxMaxConnectionTime>
            <CtxMaxDisconnectionTime>0</CtxMaxDisconnectionTime>
            <CtxMaxIdleTime>0</CtxMaxIdleTime>
            <CtxMinEncryptionLevel>0</CtxMinEncryptionLevel>
            <CtxNWLogonServer/>
            <CtxShadow>01000000</CtxShadow>
            <CtxWFHomeDir/>
            <CtxWFHomeDirDrive>D:</CtxWFHomeDirDrive>
            <CtxWFProfilePath/>
            <CtxWorkDirectory/>
            <Ctx_flag_brokenConn>false</Ctx_flag_brokenConn>
            <Ctx_flag_connectClientDrives>true</Ctx_flag_connectClientDrives>
            <Ctx_flag_connectClientPrinters>true</Ctx_flag_connectClientPrinters>
            <Ctx_flag_defaultPrinter>true</Ctx_flag_defaultPrinter>
            <Ctx_flag_inheritMode>false</Ctx_flag_inheritMode>
            <Ctx_flag_reConn>false</Ctx_flag_reConn>
            <Ctx_flag_tsLogin>false</Ctx_flag_tsLogin>
            <Ctx_shadow>1</Ctx_shadow>
            <acct_MNSLogonAccount>false</acct_MNSLogonAccount>
            <acct_accountDisabled>false</acct_accountDisabled>
            <acct_homeDirectoryRequired>false</acct_homeDirectoryRequired>
            <acct_interDomainTrust>false</acct_interDomainTrust>
            <acct_isAutoLocked>false</acct_isAutoLocked>
            <acct_normalUserAccount>true</acct_normalUserAccount>
            <acct_passwordDoesNotExpire>true</acct_passwordDoesNotExpire>
            <acct_passwordNotRequired>false</acct_passwordNotRequired>
            <acct_serverTrustAccount>false</acct_serverTrustAccount>
            <acct_temporaryDuplicateAccount>false</acct_temporaryDuplicateAccount>
            <acct_worktstationTrustAccount>false</acct_worktstationTrustAccount>
            <cn>%(givenName)s %(name)s</cn>
            <facsimileTelephoneNumber>+49-2932-916-255</facsimileTelephoneNumber>
            <gecos>%(givenName)s %(name)s</gecos>
            <gidNumber>1077</gidNumber>
            <givenName>%(givenName)s</givenName>
            <homeDirectory>/afs/gonicus.de/home/%(name)s</homeDirectory>
            <homePostalAddress>Möhnestr. 11-1759755 Arnsberg</homePostalAddress>
            <isLocked>false</isLocked>
            <l>Arnsberg</l>
            <loginShell>/bin/bash</loginShell>
            <mail>%(givenName)s.%(name)s@gonicus.de</mail>
            <mobile>015140528064</mobile>
            <o>GONICUS GmbH</o>
            <oldStorageBehavior>true</oldStorageBehavior>
            <passwordMethod>CRYPT</passwordMethod>
            <postalAddress>Möhnestr. 11-1759755 Arnsberg</postalAddress>
            <sambaAcctFlags>[UX          ]</sambaAcctFlags>
            <sambaBadPasswordCount>0</sambaBadPasswordCount>
            <sambaBadPasswordTime>1970-01-01T01:00:00</sambaBadPasswordTime>
            <sambaDomainName>GONICUS</sambaDomainName>
            <sambaKickoffTime>2038-01-19T04:14:07</sambaKickoffTime>
            <sambaLMPassword>11A1C3B7FBD02FA8E3EAED93A39C0094</sambaLMPassword>
            <sambaLogoffTime>2038-01-19T04:14:07</sambaLogoffTime>
            <sambaLogonTime>1970-01-01T01:00:00</sambaLogonTime>
            <sambaNTPassword>BDAEE20A4A9344AB43BF78D16E5556F0</sambaNTPassword>
            <sambaPrimaryGroupSID>S-1-5-21-328194278-237061239-1145748033-3155</sambaPrimaryGroupSID>
            <sambaPwdLastSet>2010-12-28T22:48:35</sambaPwdLastSet>
            <sambaSID>S-1-5-21-328194278-237061239-1145748033-3080</sambaSID>
            <shadowLastChange>2010-12-03</shadowLastChange>
            <sn>%(name)s</sn>
            <telephoneNumber>155</telephoneNumber>
            <uid>%(name)s</uid>
            <uidNumber>1040</uidNumber>
        </Attributes>
    </User>"""

entry2 = """
    <Country>
        <UUID>096cf03c-ed95-102f-823b-812492b1b75c</UUID>
        <Type>Country</Type>
        <DN>%(dn)s</DN>
        <ParentDN>%(base)s</ParentDN>
        <LastChanged>2011-06-29T09:08:25</LastChanged>
        <Attributes>
            <c></c>
            <description></description>
            <manager></manager>
            <ou></ou>
        </Attributes>
    </Country>
"""


entries = [entry1, entry2]

def get_user(name=None, givenName=None, subentries=None):
    if not name:
        name = "".join([random.choice(string.letters+string.digits) for x in range(1, 8)])
    if not givenName:
        givenName = "".join([random.choice(string.letters+string.digits) for x in range(1, 8)])
    if not subentries:
        subentries = ""

    base = choice(bases)
    entry = choice(entries)
    data = {}
    data['name'] = name
    data['givenName'] = givenName
    data['User'] = subentries
    data['base'] = base
    data['dn'] = "cn=%(name)s,%(base)s" % data
    return (entry % data,  data['dn'])


mgr = dbxml.XmlManager(dbxml.DBXML_ALLOW_EXTERNAL_ACCESS)
if mgr.existsContainer('phone4.dbxml'):
    mgr.removeContainer("phone4.dbxml")
cont = mgr.createContainer("phone4.dbxml", dbxml.DBXML_ALLOW_VALIDATION)
uc = mgr.createUpdateContext()
qc = mgr.createQueryContext()

#config = cont.getContainerConfig()
#config.setAllowValidation(True)

print "*" * 80


# Create first entry


print "Is Node container:", cont.getContainerType() == dbxml.XmlContainer.NodeContainer
print "*" * 80


display = 100
sync = 5000
reindex = 5000
compact = 5000
search = 5000
search_count = 100

cnt = []
res = ""
first = True
for i in range(10000):
    entry, dn = get_user()

    start = time.time()
    cont.putDocument(dn, """
        <root   xmlns="http://www.gonicus.de/Objects"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xsi:schemaLocation="http://www.gonicus.de/Objects new.xsd" >%s</root>
        """ % entry, uc)

    cnt.append(time.time() - start)

    if i % display == 0 and i != 0:
        print "total %s entries added | \t %s MB  | \t %s ms/each insert" % (i, \
                os.path.getsize('phone4.dbxml') / int(1024*1024), (sum(cnt) / display) * 1000)
        cnt = []

    if compact and i % compact == 0:
        print "compact ..."
        start = time.time()
        del(cont)
        mgr.compactContainer('phone4.dbxml', uc)
        cont = mgr.openContainer("phone4.dbxml")
        print "compact took %s seconds" % (int(time.time() - start))

    if reindex and i % reindex == 0:
        print "reindex ..."
        start = time.time()
        del(cont)
        mgr.reindexContainer('phone4.dbxml', uc)
        cont = mgr.openContainer("phone4.dbxml")
        print "reindex took %s seconds" % (int(time.time() - start))

    if sync and i % sync == 0:
        print "sync ... "
        start = time.time()
        cont.sync()
        print "sync took %s seconds" % (int(time.time() - start))

    if search and i % search == 0 and i != 0:
        print "search ..."
        start = time.time()
        for x in range(0,search_count):
            children = mgr.query("declare default element namespace 'http://www.gonicus.de/Objects';\
                    collection('phone4.dbxml')/root/*/name()", qc)
            #for entry in children:
            #    print entry.asString()

        print "searched started %s times, it took: %s seconds" % ( search_count, (int(time.time()-start)))


print "done"
