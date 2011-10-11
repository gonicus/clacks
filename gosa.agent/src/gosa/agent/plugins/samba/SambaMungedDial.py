from base64 import b64decode, b64encode
from binascii import hexlify, unhexlify

class SambaMungedDial(object):

    stringParams = ["CtxWorkDirectory", "CtxNWLogonServer", "CtxWFHomeDir", "CtxWFHomeDirDrive",
            "CtxWFProfilePath", "CtxInitialProgram", "CtxCallbackNumber"]
    timeParams = ["CtxMaxConnectionTime", "CtxMaxDisconnectionTime", "CtxMaxIdleTime"]

    new_header = "20002000200020002000200020002000" \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "5000"

    old_header = "6d000800200020002000200020002000" \
            "20002000200020002000200020002000"  \
            "20002000200020002000200064000100"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "20002000200020002000200020002000"  \
            "50001000"

    @staticmethod
    def encode(values):

        # Build up 'CtxCfgFlags1' property.
        flags = list(values['CtxCfgFlags1'])
        flag = int(flags[2], 16)
        if values['defaultPrinter']:
            flag |= 2
        else:
            flag &= 0xFF & ~0x2

        if values['connectClientDrives']:
            flag |= 8
        else:
            flag &= 0xFF & ~0x8

        if values['connectClientPrinters']:
            flag |= 4
        else:
            flag &= 0xFF & ~0x4
        flags[2] = hex(flag)[2:]

        flag = int(flags[5], 16)
        if values['tsLogin']:
            flag |= 1
        else:
            flag &= 0xFF & ~0x1

        if values['reConn']:
            flag |= 2
        else:
            flag &= 0xFF & ~0x2

        if values['brokenConn']:
            flag |= 4
        else:
            flag &= 0xFF & ~0x4
        flags[6] = '1' if values['inheritMode'] else '0'
        values['CtxCfgFlags1'] = ''.join(flags)

        if values['oldStorageBehavior']:
            flags = list(values['CtxCfgFlags1'])
            flags[1] = str(values['shadow'])
            values['CtxCfgFlags1'] = ''.join(flags)
        else:
            flags = list(values['CtxShadow'])
            flags[1] = str(values['shadow'])
            values['CtxShadow'] = ''.join(flags)

        params = ['CtxCfgPresent', 'CtxCfgFlags1', 'CtxCallback', 'CtxShadow',
                'CtxMaxConnectionTime', 'CtxMaxDisconnectionTime', 'CtxMaxIdleTime',
                'CtxKeyboardLayout', 'CtxMinEncryptionLevel', 'CtxWorkDirectory',
                'CtxNWLogonServer', 'CtxWFHomeDir', 'CtxWFHomeDirDrive', 'CtxWFProfilePath',
                'CtxInitialProgram', 'CtxCallbackNumber']

        result_tmp = ""
        for name in params:
            value = values[name]
            is_str = False
            if name in SambaMungedDial.stringParams:
                is_str = True
                value = value.encode('utf-16')[2:]
            elif name in SambaMungedDial.timeParams:
                usec = int(value) * 60 * 1000
                src = '%04x%04x' % (usec & 0x0FFFF, (usec & 0x0FFFF0000) >> 16)
                value = src[2:4] + src[0:2] + src[6:8] + src[4:6]

            m = SambaMungedDial.munge(name, value, is_str)
            result_tmp += m

        # First add the number of attributes
        result = unhexlify(SambaMungedDial.new_header)
        result += unhexlify('%02x00' % (len(params),))
        result += result_tmp
        result = b64encode(result)
        return result

    @staticmethod
    def munge(name, value, isString=False):

        # Encode parameter name with utf-16 and reomve the 2 Byte BOM infront of the string.
        utfName = name.encode('utf-16')[2:]

        # Set parameter length, high and low byte
        paramLen = len(utfName)
        result = ''
        result += chr(paramLen & 0x0FF)
        result += chr((paramLen & 0x0FF00) >> 8)

        # String parameters have additional trailing bytes
        valueLen = len(value);
        result += chr(valueLen & 0x0FF);
        result += chr((valueLen & 0x0FF00) >> 8)

        # Length fields have a trailing '01' appended by the UTF-16 converted name
        result += unhexlify('%02x00' % (0x1,))
        result += utfName

        # Append a trailing '00' to string parameters
        if isString and len(value):
            result += hexlify(value.decode('utf-16'))
        else:
            result += value

        return (result)


    @staticmethod
    def decode(mstr):

        # check if we've to use the old or new munged dial storage behavior
        test = b64decode(mstr)
        old_behavior  = hexlify(test)[0:2] == "6d"
        if old_behavior:
            ctxField = test[len(unhexlify(SambaMungedDial.old_header))::]
        else:
            ctxField = test[len(unhexlify(SambaMungedDial.new_header))+2::]

        # Decode parameters
        result = {}
        result['oldStorageBehavior'] = True
        while ctxField != "":

            # Get parameter-name length and parameter value length
            ctxParmNameLength = ord(ctxField[0]) + (16 * ord(ctxField[1]))
            ctxParmLength = ord(ctxField[2]) + (16 * ord(ctxField[3]))

            # Reposition ctxField on start of parameter name, read parameter name
            ctxField = ctxField[6::]
            ctxParmName = ctxField[0:ctxParmNameLength].decode('utf-16')

            # Reposition ctxField on start of parameter
            ctxField = ctxField[ctxParmNameLength::]
            ctxParm = ctxField[0:ctxParmLength]

            # If string parameter, convert
            if ctxParmName in SambaMungedDial.stringParams:
                ctxParm = unhexlify(ctxParm)

            # If time parameter, convert
            if ctxParmName in SambaMungedDial.timeParams:
                lo = ctxParm[0:4]
                hi = ctxParm[4:8] * 256
                usecs = (int(lo[2:4],16) * 256) + (int(lo[0:2], 16)) + (int(hi[2:4], 16) * 256) + (int(hi[0:2], 16) * 256 * 256)
                ctxParm = usecs / (60 * 1000)

            # Assign in result array
            result[ctxParmName]= ctxParm

            # Reposition ctxField on end of parameter and continue
            ctxField = ctxField[ctxParmLength::]

        # Add on demand flags?
        for entry in SambaMungedDial.timeParams:
            result[entry+u'Mode'] = entry in result and result[entry] != 0

        # Detect TS Login Flag
        flags = ord(result['CtxCfgFlags1'][5:6])

        result[u'tsLogin'] = bool(flags & 1)
        result[u'reConn'] =  bool(flags & 2)
        result[u'brokenConn'] =  bool(flags & 4)
        result[u'inheritMode'] = bool(result['CtxCfgFlags1'][6:7] == 1)

        if old_behavior:
            result[u'shadow'] = result['CtxCfgFlags1'][1:2]
        else:
            result[u'shadow'] = result['CtxShadow'][1:2]

        connections = int(result['CtxCfgFlags1'][2:3], 16)
        result[u'connectClientDrives'] = bool(connections & 8)
        result[u'connectClientPrinters'] = bool(connections & 4)
        result[u'defaultPrinter'] = bool(connections & 2)

        return result


