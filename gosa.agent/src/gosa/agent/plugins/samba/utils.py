# -*- coding: utf-8 -*-
import smbpasswd

from gosa.common.components import Command
from gosa.common.components import Plugin
from gosa.common.utils import N_
from gosa.common import Environment
from gosa.agent.objects.filter import ElementFilter
from gosa.agent.objects.types import AttributeType
from gosa.agent.plugins.samba.SambaMungedDial import SambaMungedDial

class SambaUtils(Plugin):
    """
    Utility class that contains methods needed to handle samba
    functionality.
    """
    _target_ = 'samba'

    def __init__(self):
        env = Environment.getInstance()
        self.env = env

    @Command(__help__=N_("Generate samba lm:nt hash combination "+
        "from the supplied password."))
    def mksmbhash(self, password):
        """
        Generate samba lm:nt hash combination.

        ========== ============
        Parameter  Description
        ========== ============
        password   Password to hash
        ========== ============

        ``Return:`` lm:nt hash combination
        """
        return '%s:%s' % smbpasswd.hash(password)


class SambaHash(ElementFilter):
    """
    An object filter which generates samba NT/LM Password hashes for the incoming value.
    """
    def __init__(self, obj):
        super(SambaHash, self).__init__(obj)

    def process(self, obj, key, valDict):
        if len(valDict[key]['value']) and type(valDict[key]['value'][0]) in [str, unicode]:
            lm, nt = smbpasswd.hash(valDict[key]['value'][0])
            valDict['sambaNTPassword'] = GOsaObjectFactory.createNewProperty(valDict[key]['backend'], 'String', value=[nt])
            valDict['sambaLMPassword'] = GOsaObjectFactory.createNewProperty(valDict[key]['backend'], 'String', value=[lm])
        else:
            raise ValueError("Unknown input type for filter %s. Type is '%s'!" % (
                self.__class__.__name__, type(valDict[key]['value'])))

            return key, valDict


class SambaMungedDialOut(ElementFilter):
    """
    Out-Filter for sambaMungedDial.
    """

    def __init__(self, obj):
        super(SambaMungedDialOut, self).__init__(obj)

    def process(self, obj, key, valDict):

        # Create a dictionary with all relevant samba attributes.
        alist = ['CtxCallback', 'CtxCallbackNumber', 'CtxCfgFlags1', 'CtxCfgPresent', \
                'CtxInitialProgram', 'CtxKeyboardLayout', 'CtxMaxConnectionTime', \
                'CtxMaxConnectionTimeMode', 'CtxMaxDisconnectionTime', \
                'CtxMaxDisconnectionTimeMode', 'CtxMaxIdleTime', \
                'CtxMaxIdleTimeMode', 'CtxMinEncryptionLevel', 'oldStorageBehavior', \
                'CtxNWLogonServer', 'CtxShadow', 'CtxWFHomeDir', 'CtxWFHomeDirDrive', \
                'CtxWFProfilePath', 'CtxWorkDirectory', 'brokenConn', 'connectClientDrives', \
                'connectClientPrinters', 'defaultPrinter', 'inheritMode', 'reConn', 'shadow', \
                'tsLogin']

        res = {}
        for entry in alist:
            if len(valDict[entry]['value']):
                res[entry]=valDict[entry]['value'][0]
            else:
                res[entry]=None

        result = SambaMungedDial.encode(res)
        valDict[key]['value'] = [result]
        return key, valDict

class SambaMungedDialIn(ElementFilter):
    """
    In-Filter for sambaMungedDial.
    """

    def __init__(self, obj):
        super(SambaMungedDialIn, self).__init__(obj)

    def process(self, obj, key, valDict):

        if len(valDict[key]['value']):

            # Create a dictionary with all relevant samba attributes.
            alist = {
                    'oldStorageBehavior': 'Boolean',
                    'CtxCallback': 'UnicodeString',
                    'CtxCallbackNumber': 'UnicodeString',
                    'CtxCfgFlags1': 'UnicodeString',
                    'CtxCfgPresent': 'UnicodeString',
                    'CtxInitialProgram': 'UnicodeString',
                    'CtxKeyboardLayout': 'UnicodeString',
                    'CtxMaxConnectionTime': 'Integer',
                    'CtxMaxConnectionTimeMode': 'Boolean',
                    'CtxMaxDisconnectionTime': 'Integer',
                    'CtxMaxDisconnectionTimeMode': 'Boolean',
                    'CtxMaxIdleTime': 'Integer',
                    'CtxMaxIdleTimeMode': 'Boolean',
                    'CtxMinEncryptionLevel': 'Integer',
                    'CtxNWLogonServer': 'UnicodeString',
                    'CtxShadow': 'UnicodeString',
                    'CtxWFHomeDir': 'UnicodeString',
                    'CtxWFHomeDirDrive': 'UnicodeString',
                    'CtxWFProfilePath': 'UnicodeString',
                    'CtxWorkDirectory': 'UnicodeString',
                    'brokenConn': 'Boolean',
                    'connectClientDrives': 'Boolean',
                    'connectClientPrinters': 'Boolean',
                    'defaultPrinter': 'Boolean',
                    'inheritMode': 'Boolean',
                    'reConn': 'Boolean',
                    'shadow': 'Integer',
                    'tsLogin': 'Boolean'}

            md = valDict[key]['value'][0]
            res = SambaMungedDial.decode(md)
            for entry in alist:
                valDict[entry]['value'] = [res[entry]]
                valDict[entry]['skip_save'] = True
        return key, valDict


class SambaAcctFlagsOut(ElementFilter):
    """
    In-Filter for sambaAcctFlags.

    Combines flag-properties into sambaAcctFlags proeprty
    """

    def __init__(self, obj):
        super(SambaAcctFlagsOut, self).__init__(obj)

    def process(self, obj, key, valDict):
        mapping = { 'D': 'accountDisabled',
                'H': 'homeDirectoryRequired',
                'I': 'interDomainTrust',
                'L': 'isAutoLocked',
                'M': 'anMNSLogonAccount',
                'N': 'passwordNotRequired',
                'S': 'serverTrustAccount',
                'T': 'temporaryDuplicateAccount',
                'U': 'normalUserAccount',
                'W': 'worktstationTrustAccount',
                'X': 'passwordDoesNotExpire'}

        # Now parse the existing acctFlags
        flagStr = ""
        for flag in mapping:
            if len(valDict[mapping[flag]]['value']) >= 1 and valDict[mapping[flag]]['value'][0]:
                flagStr += flag

        valDict[key]['value'] = ["[" + flagStr + "]"]
        return key, valDict


class SambaAcctFlagsIn(ElementFilter):
    """
    In-Filter for sambaAcctFlags.

    Each option will be transformed into a separate attribute.
    """

    def __init__(self, obj):
        super(SambaAcctFlagsIn, self).__init__(obj)

    def process(self, obj, key, valDict):
        mapping = { 'D': 'accountDisabled',
                    'H': 'homeDirectoryRequired',
                    'I': 'interDomainTrust',
                    'L': 'isAutoLocked',
                    'M': 'anMNSLogonAccount',
                    'N': 'passwordNotRequired',
                    'S': 'serverTrustAccount',
                    'T': 'temporaryDuplicateAccount',
                    'U': 'normalUserAccount',
                    'W': 'worktstationTrustAccount',
                    'X': 'passwordDoesNotExpire'}

        # Add newly introduced properties.
        for src in mapping:
            valDict[mapping[src]]['value'] = [False]
            valDict[mapping[src]]['skip_save'] = True

        # Now parse the existing acctFlags
        if len(valDict[key]['value']) >= 1:
            smbAcct = valDict[key]['value'][0]
            for src in mapping:
                if src in set(smbAcct):
                    valDict[mapping[src]]['value'] = [True]

        return key, valDict


class SambaLogonHoursAttribute(AttributeType):
    __alias__ = "SambaLogonHours"

    @classmethod
    def values_match(cls, value1, value2):
        return(str(value1) == str(value2))

    @classmethod
    def is_valid_value(cls, value):

        if value:

            # Check if we've got a dict with values for all seven week days.
            if value[0].keys() != range(0,7):
                return False

            # Check if each week day contains 24 values.
            for i in range(0,7):
                if type(value[0][i]) != str or len(value[0][i]) != 24 or len(set(value[0][i]) - set('01')):
                    return False

        return True

    @classmethod
    def _convert_to_unicodestring(cls, value):

        if len(value):

            # Combine the binary strings
            val = value[0]
            lstr = ""
            for day in range(0,7):
                lstr += val[day]

            # New reverse every 8 bit part, and toggle high- and low-tuple (4Bits)
            new = ""
            for i in range(0, 21):
                n = lstr[i*8:((i+1)*8)]
                n = n[0:4] + n[4:]
                n = n[::-1]
                n = str(hex(int( n, 2)))[2::].rjust(2,'0')
                new += n
            value = [new.upper()]

        return(value)

    @classmethod
    def _convert_from_unicodestring(cls, value):

        if len(value):

            # Convert each hex-pair into binary values.
            # Then reverse the binary result and switch high and low pairs.
            res = {}
            value = value[0]
            lstr = ""
            for i in range(0,42,2):
                n = (bin(int(value[i:i+2], 16))[2::]).rjust(8, '0')
                n = n[::-1]
                lstr += n[0:4] + n[4:]

            # Parse result into more readable value
            for day in range(0,7):
                res[day] = lstr[(day*24):((day+1)*24)]
            value = [res]

        return(value)
