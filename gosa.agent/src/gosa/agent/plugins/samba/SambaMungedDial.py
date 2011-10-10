from base64 import b64decode
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

    @classmethod
    def decode(self, mstr):

        # check if we've to use the old or new munged dial storage behavior
        test = b64decode(mstr)
        old_behavior  = hexlify(test)[0:2] == "6d"
        if old_behavior:
          ctxField = test[len(unhexlify(SambaMungedDial.old_header))::]
        else:
          ctxField = test[len(unhexlify(SambaMungedDial.new_header))+2::]

        # Decode parameters
        result = {}
        result['old_behaviour'] = True
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
        result[u'CtxMaxConnectionTimeF'] = True if ('CtxMaxConnectionTime' in result and result['CtxMaxConnectionTime']) else False
        result[u'CtxMaxDisconnectionTimeF'] = True if ('CtxMaxDisconnectionTime' in result and result['CtxMaxDisconnectionTime']) else False
        result[u'CtxMaxIdleTimeF'] = True if ('CtxMaxIdleTime' in result and result['CtxMaxIdleTime']) else False

        return result


