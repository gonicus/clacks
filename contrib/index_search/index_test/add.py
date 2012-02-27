# -*- coding: utf-8 -*- #
import dbxml
import random
import string
import time

dummy_entry = """
    <User  xmlns="http://www.gonicus.de/Objects"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.gonicus.de/Objects objects.xsd">%(User)s
        <UUID>096cf03c-ed95-102f-823b-812492b1b75c</UUID>
        <Type>User</Type>
        <DN>cn=%(givenName)s %(name)s,ou=people,ou=Technik,dc=gonicus,dc=de</DN>
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


def get_user(name=None, givenName=None, subentries=None):
    if not name:
        name = "".join([random.choice(string.letters+string.digits) for x in range(1, 8)])
    if not givenName:
        givenName = "".join([random.choice(string.letters+string.digits) for x in range(1, 8)])
    if not subentries:
        subentries = ""

    data = {}
    data['name'] = name
    data['givenName'] = givenName
    data['User'] = subentries
    return dummy_entry % data


mgr = dbxml.XmlManager(dbxml.DBXML_ALLOW_EXTERNAL_ACCESS)
if mgr.existsContainer('phone4.dbxml'):
    mgr.removeContainer("phone4.dbxml")
cont = mgr.createContainer("phone4.dbxml", dbxml.DBXML_ALLOW_VALIDATION)
uc = mgr.createUpdateContext()
qc = mgr.createQueryContext()


print "*" * 80
print "Is Node container:", cont.getContainerType() == dbxml.XmlContainer.NodeContainer
print "Autoindex is: Off", cont.setAutoIndexing(False, uc)


# Create first entry
print "Add initial doc"
entry = get_user('test','test')
cont.putDocument("test", entry, uc)
print "... done"


print "*" * 80
print "start adding more:"

res = ""
mod = 50
cnt = []
for i in range(10000):

    query = """
            declare default element namespace 'http://www.gonicus.de/Objects';
            insert nodes
                %s
            before collection('phone4.dbxml')/User/UUID
            """ %  get_user()

    start = time.time()
    res = mgr.query(query, qc)
    if i % mod == 0:
        print "%s entries" % (i), sum(cnt) / mod
    else:
        cnt.append(time.time() - start)

start = time.time()
res = mgr.query("collection('phone4.dbxml')//name()", qc)
print res
print time.time() - start


print "Index wieder an!"
cont.setAutoIndexing(True, uc)
cont.sync()
cont.close()

print "done"